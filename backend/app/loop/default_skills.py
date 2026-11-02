"""Built-in baseline Skills used by the real runtime and the admin demo.

These are idempotent, executable workflow policies rather than display-only rows.
They provide a safe baseline before enough production traces exist for Skill Miner.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.storage.store import DataStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_SKILLS: list[dict[str, Any]] = [{'_id': 'skill_dept_hqaq_emergency_seed',
  'name': '图像材料补充导航',
  'description': '图像材料补充导航：按来源核对证据并组织回答。',
  'dept_id': 'dept_hqaq',
  'scope': 'department',
  'trigger': {'intent_patterns': ['图片', '模糊', '裁剪', 'OCR', '面单', '透视', '锐化', '超分', '看不清'],
              'entities_required': ['matter'],
              'confidence_threshold': 0.75},
  'action': {'type': 'workflow',
             'steps': [{'step': 1, 'action': 'extract_entity', 'params': {'entity': 'matter'}},
                       {'step': 2,
                        'action': 'retrieve',
                        'params': {'query': '{matter} 图片 清晰度 原图 OCR 凭证', 'top_k': 8}},
                       {'step': 3, 'action': 'generate', 'params': {'template': '问题-所需材料-核验边界'}}]},
  'unique_rules': ['文档描述的是业务流程和能力，不代表工具已执行；不得生成实时价格、真伪结论、到账时限。'],
  'rubric_rules': ['说明已有证据、缺少的材料及下一步核验渠道，关键结论附来源。']},
 {'_id': 'skill_dept_zfxy_procedure_seed',
  'name': '售后理赔步骤导航',
  'description': '售后理赔步骤导航：按来源核对证据并组织回答。',
  'dept_id': 'dept_zfxy',
  'scope': 'department',
  'trigger': {'intent_patterns': ['售后', '理赔', '破损', '瑕疵', '投诉', '描述不符', '凭证'],
              'entities_required': ['matter'],
              'confidence_threshold': 0.72},
  'action': {'type': 'workflow',
             'steps': [{'step': 1, 'action': 'extract_entity', 'params': {'entity': 'matter'}},
                       {'step': 2,
                        'action': 'retrieve',
                        'params': {'query': '{matter} 商品破损 购买凭证 理赔 平台规则', 'top_k': 7}},
                       {'step': 3, 'action': 'generate', 'params': {'template': '前置材料-申请步骤-待确认事项'}}]},
  'unique_rules': ['文档描述的是业务流程和能力，不代表工具已执行；不得生成实时价格、真伪结论、到账时限。'],
  'rubric_rules': ['说明已有证据、缺少的材料及下一步核验渠道，关键结论附来源。']},
 {'_id': 'skill_academic_deadline_seed',
  'name': '客服时效与实时事实核验',
  'description': '客服时效与实时事实核验：按来源核对证据并组织回答。',
  'dept_id': '',
  'scope': 'global',
  'trigger': {'intent_patterns': ['到账', '什么时候', '最晚', '历史价格', '当前价格'],
              'entities_required': ['matter'],
              'confidence_threshold': 0.78},
  'action': {'type': 'workflow',
             'steps': [{'step': 1,
                        'action': 'retrieve',
                        'params': {'query': '{matter} 时间窗口 来源 实时状态 平台规则', 'top_k': 8}},
                       {'step': 2, 'action': 'call_tool', 'params': {'tool': 'calendar_lookup'}},
                       {'step': 3, 'action': 'generate', 'params': {'template': '已知信息-缺失证据-核验渠道'}}]},
  'unique_rules': ['文档描述的是业务流程和能力，不代表工具已执行；不得生成实时价格、真伪结论、到账时限。'],
  'rubric_rules': ['说明已有证据、缺少的材料及下一步核验渠道，关键结论附来源。']}]


async def seed_default_skills(store: DataStore) -> int:
    created = 0
    for template in DEFAULT_SKILLS:
        if await store.get_skill(template["_id"]) is not None:
            continue
        skill = {
            **template, "metrics": {
                "trigger_count": 0, "success_count": 0, "success_rate": 0.0,
                "avg_latency_ms": 0, "last_triggered": "",
            },
            "version": 1, "status": "active", "auto_generated": False,
            "confidence": 1.0, "gray_percent": 1.0, "created_by": "system_seed",
            "origin": "builtin_baseline", "created_at": _now(),
        }
        await store.upsert_skill(skill)
        await store.upsert("strategy_versions", {
            "_id": f"strategy_version_{skill['_id']}_v1_seed",
            "artifact_id": skill["_id"], "artifact_type": "skill", "version": 1,
            "reason": "builtin_baseline_seeded", "snapshot": skill, "created_at": _now(),
        })
        created += 1
    return created
