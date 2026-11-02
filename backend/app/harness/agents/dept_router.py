"""Dept Router（自动部门路由 Agent）：把客服问题匹配到最符合的部门。

策略：关键词精确匹配（快速、可解释）→ LLM 语义路由（兜底）→ 全部部门。
返回路由结果（dept_ids / matched_by / confidence / reasons / dept_names），
供前端展示"已自动路由到 XX 部门"。
"""
from __future__ import annotations

from typing import Any

from app.llm.client import ChatMessage, LLMClient
from app.storage.store import DataStore
from app.utils.logging import get_logger

logger = get_logger(__name__)

# 部门关键词路由表（覆盖全部部门；命中即路由到对应部门，可多部门）
DEPT_KEYWORDS: dict[str, list[str]] = {'dept_jwc': ['商品', 'SKU', '型号', '同款', '品牌', '商品识别', '商品检索', '以图搜图'],
 'dept_xsc': ['比价', '价格', '到手价', '历史低价', '优惠券', '划算', '折扣', '导购'],
 'dept_cwc': ['退款', '退货', '到账', '原路退回', '仅退款', '退货退款'],
 'dept_rsc': ['订单', '物流', '单号', '发货', '收货地址', '快递', '催发货', '滞留'],
 'dept_yjsy': ['二手', '鉴定', '真伪', '正品', '防伪', '鞋标', '鞋盒', '仿品'],
 'dept_zfxy': ['售后', '理赔', '破损', '瑕疵', '投诉', '描述不符', '凭证'],
 'dept_hqaq': ['图片', '模糊', '裁剪', 'OCR', '面单', '透视', '锐化', '超分', '看不清']}

ROUTE_PROMPT = """你是部门路由助手。判断客服问题最应由哪个部门回答，输出 JSON：
{{"depts": ["dept_id"], "confidence": 0.0-1.0, "reason": "简短理由"}}

候选部门：
{departments}

客服问题：{query}
"""


class DeptRouter:
    """自动部门路由：客服问题 → 最匹配的部门。"""

    def __init__(self, llm: LLMClient, store: DataStore) -> None:
        self.llm = llm
        self.store = store

    async def route(self, query: str) -> dict[str, Any]:
        departments = await self.store.list_departments()
        dept_names = {d["_id"]: d.get("name", d["_id"]) for d in departments}
        valid = set(dept_names)

        # 1) 关键词精确匹配（快速、可解释）
        matched, reasons = self._keyword_match(query, valid)
        if matched:
            return self._result(matched, "keyword", min(0.95, 0.6 + 0.1 * len(matched)), reasons, dept_names)

        # 2) LLM 语义路由（关键词未命中时）
        try:
            dept_desc = ", ".join(f"{d['_id']}({d.get('name', '')})" for d in departments) or "dept_all(通用)"
            data = await self.llm.complete_json(
                [ChatMessage.system("你是部门路由助手。"), ChatMessage.user(ROUTE_PROMPT.format(departments=dept_desc, query=query))],
                temperature=0.0,
            )
            depts = [d for d in (data.get("depts") or []) if d in valid]
            if depts:
                return self._result(depts, "llm", float(data.get("confidence", 0.7)), [data.get("reason", "")], dept_names)
        except Exception as exc:  # noqa: BLE001
            logger.warning("部门路由 LLM 失败(%s)，回退全部部门", exc)

        # 3) 全部部门（未命中）
        return self._result([], "all", 0.3, ["未匹配到特定部门，检索全部部门"], dept_names)

    @staticmethod
    def _keyword_match(query: str, valid: set[str]) -> tuple[list[str], list[str]]:
        matched: list[str] = []
        reasons: list[str] = []
        for dept, kws in DEPT_KEYWORDS.items():
            if dept not in valid:
                continue
            hits = [k for k in kws if k in query]
            if hits:
                matched.append(dept)
                reasons.append(f"命中关键词「{hits[0]}」")
        return matched, reasons

    @staticmethod
    def _result(dept_ids: list[str], matched_by: str, confidence: float, reasons: list[str], dept_names: dict[str, str]) -> dict[str, Any]:
        return {
            "dept_ids": dept_ids,
            "dept_names": [dept_names.get(d, d) for d in dept_ids],
            "matched_by": matched_by,
            "confidence": round(float(confidence), 2),
            "reasons": reasons,
        }
