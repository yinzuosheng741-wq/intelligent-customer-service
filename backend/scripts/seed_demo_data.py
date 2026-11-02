"""生成客服演示文档、审核单、合成反馈与业务组 Skill。用法：python -m scripts.seed_demo_data。"""
from __future__ import annotations

import asyncio
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.deps import build_container


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# 可选业务组迁移映射；默认不迁移或删除任何业务组。
MIGRATE_MAP = {}
DELETE_DEPTS = []


# =====================================================================
# 各部门模拟数据：skill / docs / badcases / review_qa
# =====================================================================
DEPT_DATA: list[dict[str, Any]] = [{'dept_id': 'dept_jwc',
  'skill': {'name': '商品定位与检索指南',
            'keywords': ['商品', 'SKU', '型号', '同款', '品牌', '商品识别', '商品检索', '以图搜图'],
            'unique_rules': ['实时状态必须来自授权业务接口；知识库只说明流程。', '未提供的价格、时限、真伪结论和理赔结果不得补全。']},
  'docs': [{'title': '商品定位与检索指南',
            'status': 'active',
            'content': '# 商品定位与检索指南\n'
                       '\n'
                       '## 来源与适用范围\n'
                       '\n'
                       '资料来源：电商客服场景知识规范（参见 '
                       'docs/knowledge-sources.md）。以下为项目流程知识整理，不是平台正式规则或实时业务结果。\n'
                       '\n'
                       '## 业务流程与证据要求\n'
                       '\n'
                       '商品定位应先确认唯一 '
                       'SKU；商品名模糊时先进行文字检索确认商品。以图搜图用于定位品牌、型号和相似商品，不能把视觉相似直接当作同款或真伪结论。外部网页只作为补充来源，需要核对时效和商品规格。\n'}],
  'badcases': [{'query': '商品名模糊时应先确认什么？',
                'bad_answer': '无需核实，可以直接保证结果。',
                'signal': 'correction',
                'rule': '不得把流程说明或示例当成当前订单事实。'}],
  'review_qa': [{'question': '商品名模糊时应先确认什么？', 'expected': '唯一 SKU', 'answer': '唯一 SKU'}]},
 {'dept_id': 'dept_xsc',
  'skill': {'name': '比价与历史价格咨询指南',
            'keywords': ['比价', '价格', '到手价', '历史低价', '优惠券', '划算', '折扣', '导购'],
            'unique_rules': ['实时状态必须来自授权业务接口；知识库只说明流程。', '未提供的价格、时限、真伪结论和理赔结果不得补全。']},
  'docs': [{'title': '比价与历史价格咨询指南',
            'status': 'active',
            'content': '# 比价与历史价格咨询指南\n'
                       '\n'
                       '## 来源与适用范围\n'
                       '\n'
                       '资料来源：电商客服场景知识规范（参见 '
                       'docs/knowledge-sources.md）。以下为项目流程知识整理，不是平台正式规则或实时业务结果。\n'
                       '\n'
                       '## 业务流程与证据要求\n'
                       '\n'
                       '跨平台比价需对照同款商品、规格和到手价。历史价格查询使用近30天、90天、180天的价格记录，关注历史最低价、价格百分位和近30天趋势。说明文中的399元和379元是示例，不是任何商品的当前价格。本项目未连接实时报价接口，不能输出当前最低价或声称已领取优惠券。\n'}],
  'badcases': [{'query': '历史价格查询涉及哪些时间窗口？',
                'bad_answer': '无需核实，可以直接保证结果。',
                'signal': 'correction',
                'rule': '不得把流程说明或示例当成当前订单事实。'}],
  'review_qa': [{'question': '历史价格查询涉及哪些时间窗口？', 'expected': '30天、90天、180天', 'answer': '30天、90天、180天'}]},
 {'dept_id': 'dept_cwc',
  'skill': {'name': '退款类型与进度咨询指南',
            'keywords': ['退款', '退货', '到账', '原路退回', '仅退款', '退货退款'],
            'unique_rules': ['实时状态必须来自授权业务接口；知识库只说明流程。', '未提供的价格、时限、真伪结论和理赔结果不得补全。']},
  'docs': [{'title': '退款类型与进度咨询指南',
            'status': 'active',
            'content': '# 退款类型与进度咨询指南\n'
                       '\n'
                       '## 来源与适用范围\n'
                       '\n'
                       '资料来源：电商客服场景知识规范（参见 '
                       'docs/knowledge-sources.md）。以下为项目流程知识整理，不是平台正式规则或实时业务结果。\n'
                       '\n'
                       '## 业务流程与证据要求\n'
                       '\n'
                       '申请退款包含仅退款和退货退款两种类型。退款进度需以授权业务系统的申请状态为准，区分处理中与已到账，并核对退款路径，如原路退回或余额。项目资料没有给出统一到账时限。当前系统只提供流程说明，不能声称已经提交退款、查询到个人进度或保证到账日期。\n'}],
  'badcases': [{'query': '退款申请有哪些类型？',
                'bad_answer': '无需核实，可以直接保证结果。',
                'signal': 'correction',
                'rule': '不得把流程说明或示例当成当前订单事实。'}],
  'review_qa': [{'question': '退款申请有哪些类型？', 'expected': '仅退款、退货退款', 'answer': '仅退款、退货退款'}]},
 {'dept_id': 'dept_rsc',
  'skill': {'name': '订单物流与地址处理指南',
            'keywords': ['订单', '物流', '单号', '发货', '收货地址', '快递', '催发货', '滞留'],
            'unique_rules': ['实时状态必须来自授权业务接口；知识库只说明流程。', '未提供的价格、时限、真伪结论和理赔结果不得补全。']},
  'docs': [{'title': '订单物流与地址处理指南',
            'status': 'active',
            'content': '# 订单物流与地址处理指南\n'
                       '\n'
                       '## 来源与适用范围\n'
                       '\n'
                       '资料来源：电商客服场景知识规范（参见 '
                       'docs/knowledge-sources.md）。以下为项目流程知识整理，不是平台正式规则或实时业务结果。\n'
                       '\n'
                       '## 业务流程与证据要求\n'
                       '\n'
                       '订单详情包含订单状态、商品信息、支付金额和物流单号等。物流轨迹查询需要授权接口返回最新位置及异常原因。通常在商家未发货前引导用户修改收货地址；具体平台是否可改仍需当前平台规则确认。催发货需要接入业务系统，不能将文字回复当作已经催单。\n'}],
  'badcases': [{'query': '物流查询需要核对哪个编号？',
                'bad_answer': '无需核实，可以直接保证结果。',
                'signal': 'correction',
                'rule': '不得把流程说明或示例当成当前订单事实。'}],
  'review_qa': [{'question': '物流查询需要核对哪个编号？', 'expected': '物流单号', 'answer': '物流单号'}]},
 {'dept_id': 'dept_yjsy',
  'skill': {'name': '二手商品鉴定取证指南',
            'keywords': ['二手', '鉴定', '真伪', '正品', '防伪', '鞋标', '鞋盒', '仿品'],
            'unique_rules': ['实时状态必须来自授权业务接口；知识库只说明流程。', '未提供的价格、时限、真伪结论和理赔结果不得补全。']},
  'docs': [{'title': '二手商品鉴定取证指南',
            'status': 'active',
            'content': '# 二手商品鉴定取证指南\n'
                       '\n'
                       '## 来源与适用范围\n'
                       '\n'
                       '资料来源：电商客服场景知识规范（参见 '
                       'docs/knowledge-sources.md）。以下为项目流程知识整理，不是平台正式规则或实时业务结果。\n'
                       '\n'
                       '## 业务流程与证据要求\n'
                       '\n'
                       '鉴定需要清晰的鞋标、鞋盒标签、防伪码和购买凭证等材料。先定位品牌型号，再查品牌官方鉴定标准，必要时通过品牌官方防伪接口核对编码状态及首次激活记录。图片相似、OCR '
                       '文字和模型观察都不能单独证明正品或假货。证据不足应请求补图或引导平台专业鉴定。当前系统未接品牌接口，不得给出确定真伪结论。\n'}],
  'badcases': [{'query': '二手鉴定证据不足时应怎么办？',
                'bad_answer': '无需核实，可以直接保证结果。',
                'signal': 'correction',
                'rule': '不得把流程说明或示例当成当前订单事实。'}],
  'review_qa': [{'question': '二手鉴定证据不足时应怎么办？', 'expected': '请求补图、平台专业鉴定', 'answer': '请求补图、平台专业鉴定'}]},
 {'dept_id': 'dept_zfxy',
  'skill': {'name': '售后理赔与投诉材料指南',
            'keywords': ['售后', '理赔', '破损', '瑕疵', '投诉', '描述不符', '凭证'],
            'unique_rules': ['实时状态必须来自授权业务接口；知识库只说明流程。', '未提供的价格、时限、真伪结论和理赔结果不得补全。']},
  'docs': [{'title': '售后理赔与投诉材料指南',
            'status': 'active',
            'content': '# 售后理赔与投诉材料指南\n'
                       '\n'
                       '## 来源与适用范围\n'
                       '\n'
                       '资料来源：电商客服场景知识规范（参见 '
                       'docs/knowledge-sources.md）。以下为项目流程知识整理，不是平台正式规则或实时业务结果。\n'
                       '\n'
                       '## 业务流程与证据要求\n'
                       '\n'
                       '售后理赔场景包括商品破损和与描述不符。应保留商品瑕疵照片、购买凭证，必要时补充面单和物流信息，再按平台页面要求申请理赔或投诉。鉴定和理赔是两个环节，疑似非正品不等于平台已经批准赔付。资料未提供赔付倍数、统一审核周期或商家响应时限，应以适用平台正式规则为准。\n'}],
  'badcases': [{'query': '商品理赔常见凭证有哪些？',
                'bad_answer': '无需核实，可以直接保证结果。',
                'signal': 'correction',
                'rule': '不得把流程说明或示例当成当前订单事实。'}],
  'review_qa': [{'question': '商品理赔常见凭证有哪些？', 'expected': '商品瑕疵照片、购买凭证', 'answer': '商品瑕疵照片、购买凭证'}]},
 {'dept_id': 'dept_hqaq',
  'skill': {'name': '图像材料质量与取证指南',
            'keywords': ['图片', '模糊', '裁剪', 'OCR', '面单', '透视', '锐化', '超分', '看不清'],
            'unique_rules': ['实时状态必须来自授权业务接口；知识库只说明流程。', '未提供的价格、时限、真伪结论和理赔结果不得补全。']},
  'docs': [{'title': '图像材料质量与取证指南',
            'status': 'active',
            'content': '# 图像材料质量与取证指南\n'
                       '\n'
                       '## 来源与适用范围\n'
                       '\n'
                       '资料来源：电商客服场景知识规范（参见 '
                       'docs/knowledge-sources.md）。以下为项目流程知识整理，不是平台正式规则或实时业务结果。\n'
                       '\n'
                       '## 业务流程与证据要求\n'
                       '\n'
                       '图片目标过小时可裁剪 crop；倾斜标签或面单可透视矫正 perspective_correct；低分辨率可考虑 super_resolution；边缘模糊可考虑 '
                       'sharpen；商品说明书和快递面单可通过 layout_parsing 做结构化 '
                       'OCR。增强可能引入伪细节，识别结果仍须回查原图和权威来源。本项目只复用这些能力的适用知识，没有注册这些图像处理工具，用户应提供可读文字或已有解析结果。\n'}],
  'badcases': [{'query': '倾斜快递面单对应哪种预处理？',
                'bad_answer': '无需核实，可以直接保证结果。',
                'signal': 'correction',
                'rule': '不得把流程说明或示例当成当前订单事实。'}],
  'review_qa': [{'question': '倾斜快递面单对应哪种预处理？',
                 'expected': '透视矫正、perspective_correct',
                 'answer': '透视矫正、perspective_correct'}]}]


# =====================================================================
async def migrate_departments(container) -> None:
    store = container.store
    for from_dept, to_dept in MIGRATE_MAP.items():
        moved = 0
        # documents
        for d in await store.list_documents(dept_id=from_dept):
            d["dept_id"] = to_dept
            await store.upsert("documents", d)
            moved += 1
        # chunks
        for c in await store.list_all_chunks(dept_id=from_dept):
            c["dept_id"] = to_dept
            await store.upsert("chunks", c)
        # doc_relations
        for r in await store.list_relations():
            changed = False
            if r.get("from_dept") == from_dept:
                r["from_dept"] = to_dept
                changed = True
            if r.get("to_dept") == from_dept:
                r["to_dept"] = to_dept
                changed = True
            if changed:
                await store.upsert("doc_relations", r)
        # review orders
        for o in await store.list_review_orders(dept_id=from_dept):
            o["dept_id"] = to_dept
            await store.upsert("review_orders", o)
        # test questions
        for q in await store.list_test_questions(dept_id=from_dept):
            q["dept_id"] = to_dept
            await store.upsert("test_questions", q)
        print(f"[迁移] {from_dept} -> {to_dept}: 文档 {moved} 份（含 chunks/关联/审核单/题库）")

    for dept_id in DELETE_DEPTS:
        if await store.get_department(dept_id) is not None:
            await store.delete("departments", dept_id)
            await store.delete("dept_memory", dept_id)
            print(f"[合并] 已删除冗余部门 {dept_id}")


async def seed_docs(container) -> None:
    store = container.store
    tmp_dir = Path(tempfile.mkdtemp(prefix="wenshu_seed_"))
    try:
        for item in DEPT_DATA:
            dept_id = item["dept_id"]
            existing = {d.get("title") for d in await store.list_documents(dept_id=dept_id)}
            for spec in item["docs"]:
                title = spec["title"]
                if title in existing:
                    print(f"[跳过] 已存在 {dept_id}《{title}》")
                    continue
                fp = tmp_dir / f"{title}.md"
                fp.write_text(spec["content"], encoding="utf-8")
                try:
                    doc = await container.indexer.ingest(str(fp), dept_id=dept_id, uploaded_by="seed_demo")
                    # 设置不同状态 + 记录 pipeline 阶段
                    await store.update_document(doc["_id"], {
                        "status": spec["status"],
                        "pipeline_stages": [
                            {"key": "upload", "name": "上传", "done": True},
                            {"key": "parse", "name": "格式解析", "done": True},
                            {"key": "clean", "name": "清洗", "done": True},
                            {"key": "chunk", "name": "语义切片", "done": True, "detail": f"{doc.get('chunk_count', 0)} 切片"},
                            {"key": "metadata", "name": "元数据提取", "done": True, "detail": doc.get("doc_type", "other")},
                            {"key": "vectorize", "name": "向量化", "done": doc.get("vector_status") == "ready"},
                            {"key": "index", "name": "索引构建", "done": doc.get("vector_status") == "ready"},
                            {"key": "relations", "name": "跨部门关联挖掘", "done": True, "detail": "0 关联"},
                        ],
                    })
                    print(f"[文档] {dept_id}《{title}》(status={spec['status']}, {doc.get('chunk_count', 0)} chunks)")
                except Exception as exc:  # noqa: BLE001
                    print(f"[失败] {dept_id}《{title}》: {exc}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def seed_review_orders(container) -> None:
    store = container.store
    for item in DEPT_DATA:
        dept_id = item["dept_id"]
        order_id = f"review_{dept_id}_seed"
        if await store.get_review_order(order_id) is not None:
            print(f"[跳过] 审核单已存在 {order_id}")
            continue
        qa_pairs = [
            {
                "question": q["question"],
                "expected": q["expected"],
                "answer": q["answer"],
                "citations": [],
                "confidence": 0.8,
                "verdict": None,
                "correct": None,
                "correction": "",
            }
            for q in item["review_qa"]
        ]
        order = {
            "_id": order_id,
            "dept_id": dept_id,
            "doc_id": "",
            "doc_title": item["skill"]["name"] + "（模拟审核单）",
            "status": "pending",
            "qa_pairs": qa_pairs,
            "total": len(qa_pairs),
            "correct": 0,
            "accuracy": None,
            "created_at": _now(),
            "reviewed_at": None,
            "reviewed_by": None,
        }
        await store.insert_review_order(order)
        print(f"[审核单] {dept_id} 生成待审核单 {order_id} ({len(qa_pairs)} 题)")


async def seed_badcases_and_skills(container) -> None:
    store = container.store
    for item in DEPT_DATA:
        dept_id = item["dept_id"]
        skill_spec = item["skill"]

        # 1) badcase：写入 feedback + traces（供 Loop Reflect）
        #    演示 badcase 每次重跑都恢复为"未消费"，保证"手动触发 Loop"始终有反馈可观察
        for i, bc in enumerate(item["badcases"]):
            fb_id = f"fb_{dept_id}_{i}"
            await store.upsert("feedback", {
                "_id": fb_id,
                "session_id": "",
                "user_id": "student",
                "query": bc["query"],
                "answer": bc["bad_answer"],
                "kind": "explicit",
                "signal": bc["signal"],
                "detail": {"root_cause": "retrieval" if bc["signal"] == "down" else "generation", "rule": bc["rule"], "dept_id": dept_id},
                "consumed": False,
                "created_at": _now(),
            })
            trace_id = f"trace_{dept_id}_bad_{i}"
            if await store.get("traces", trace_id) is None:
                await store.upsert("traces", {
                    "_id": trace_id,
                    "session_id": "",
                    "user_id": "student",
                    "query": bc["query"],
                    "answer": bc["bad_answer"],
                    "intent": {"type": "regulation_consult", "depts": [dept_id]},
                    "verification": {"passed": False, "score": 0.4, "issues": [bc["rule"]]},
                    "latency_ms": 1200,
                    "success": False,
                    "created_at": _now(),
                })

        # 1.5) good case：正确回答的 👍 反馈（用于计算回答采纳率，标记已消费、不进入 Loop 队列）
        for g_i, gq in enumerate(item["review_qa"][:1]):
            await store.upsert("feedback", {
                "_id": f"fb_{dept_id}_up_{g_i}",
                "session_id": "",
                "user_id": "student",
                "query": gq["question"],
                "answer": gq["answer"],
                "kind": "explicit",
                "signal": "up",
                "detail": {},
                "consumed": True,
                "created_at": _now(),
            })

        # 2) 初始 skill：unique_rules（部门独特规则）+ rubric_rules（初始为空，运行 Loop 后由 Reflect 沉淀）
        skill_id = f"skill_{dept_id}_seed"
        skill = {
            "_id": skill_id,
            "name": skill_spec["name"],
            "dept_id": dept_id,
            "scope": "department",
            "trigger": {
                "intent_patterns": skill_spec["keywords"],
                "entities_required": ["matter"],
                "confidence_threshold": 0.75,
            },
            "action": {
                "type": "workflow",
                "steps": [
                    {"step": 1, "action": "extract_entity", "params": {"entity": "matter"}},
                    {"step": 2, "action": "retrieve", "params": {"query": "{matter} 相关制度", "top_k": 5}},
                    {"step": 3, "action": "generate", "params": {"template": "department"}},
                ],
            },
            "unique_rules": skill_spec["unique_rules"],
            "rubric_rules": [],
            "metrics": {"trigger_count": 0, "success_rate": 0.0, "avg_latency_ms": 0, "last_triggered": ""},
            "version": 1,
            "status": "active",
            "auto_generated": False,
            "created_by": "seed",
            "created_at": _now(),
        }
        await store.upsert_skill(skill)
        print(f"[badcase] {dept_id} 已准备 {len(item['badcases'])} 条未消费反馈 + {len(item['badcases'])} 条失败 trace + 1 条 👍 反馈")
        print(f"[Skill] {dept_id} 初始技能《{skill_spec['name']}》：{len(skill_spec['unique_rules'])} 条独特规则（rubric 规则运行 Loop 后沉淀）")


async def main() -> None:
    settings = get_settings()
    container = build_container(settings)
    if container.mongo is not None:
        await container.mongo.connect()
    if hasattr(container.session_store, "connect"):
        try:
            await container.session_store.connect()
        except Exception:
            pass

    print("== 1/4 合并部门 + 迁移误归文件 ==")
    await migrate_departments(container)

    print("\n== 2/4 每部门生成 3 份模拟文档（active/review/draft） ==")
    await seed_docs(container)

    print("\n== 3/4 每部门生成待审核单 ==")
    await seed_review_orders(container)

    print("\n== 4/4 生成 badcase 并反思出 rubric 规则写入初始 Skill ==")
    await seed_badcases_and_skills(container)

    print("\n完成。")
    if container.mongo is not None:
        await container.mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
