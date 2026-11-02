"""种子数据：部门 / 术语表 / FAQ / 校历 / 默认 Rules&Hooks。

用法：python -m scripts.seed_data
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.config import get_settings
from app.deps import build_container
from app.loop.default_skills import seed_default_skills

DEPARTMENTS = [{'_id': 'dept_jwc', 'name': '商品识别与检索组', 'name_en': 'Product Retrieval', 'category': 'academic'},
 {'_id': 'dept_xsc', 'name': '比价导购组', 'name_en': 'Price Advisory', 'category': 'student'},
 {'_id': 'dept_cwc', 'name': '退款服务组', 'name_en': 'Refund Service', 'category': 'finance'},
 {'_id': 'dept_rsc', 'name': '订单物流组', 'name_en': 'Order Logistics', 'category': 'admin'},
 {'_id': 'dept_yjsy', 'name': '二手鉴定组', 'name_en': 'Authentication Advisory', 'category': 'academic'},
 {'_id': 'dept_zfxy', 'name': '售后理赔组', 'name_en': 'Claims Service', 'category': 'academic'},
 {'_id': 'dept_hqaq', 'name': '图像材料支持组', 'name_en': 'Visual Evidence Support', 'category': 'logistics'}]

GLOSSARY = [{'canonical': 'SKU', 'synonyms': ['商品编号', '货号', '库存单位']},
 {'canonical': '到手价', 'synonyms': ['券后价', '实付价']},
 {'canonical': '历史价格', 'synonyms': ['价格走势', '历史低价']},
 {'canonical': '以图搜图', 'synonyms': ['图片检索', 'image_search']},
 {'canonical': '文字检索', 'synonyms': ['关键词检索', 'text_search']},
 {'canonical': '网页搜索', 'synonyms': ['web_search']},
 {'canonical': '版面解析', 'synonyms': ['OCR', 'layout_parsing', '面单识别']},
 {'canonical': '裁剪', 'synonyms': ['crop', '局部放大']},
 {'canonical': '透视矫正', 'synonyms': ['perspective_correct', '倾斜校正']},
 {'canonical': '超分辨率', 'synonyms': ['super_resolution', '低分辨率增强']},
 {'canonical': '锐化', 'synonyms': ['sharpen', '边缘增强']},
 {'canonical': '防伪码验证', 'synonyms': ['防伪查询', '查防伪码']},
 {'canonical': '退货退款', 'synonyms': ['退货并退款']},
 {'canonical': '仅退款', 'synonyms': ['不退货退款']},
 {'canonical': '物流轨迹', 'synonyms': ['快递进度', '包裹位置']},
 {'canonical': '申请理赔', 'synonyms': ['破损索赔', '描述不符理赔']},
 {'canonical': '鉴定报告', 'synonyms': ['鉴定结果', '平台鉴定结论']}]

CALENDAR = {'scenario': '电商客服', 'source': '电商客服场景知识规范', 'notice': '未提供平台活动日历、退款时限或审核周期，不得推算或承诺具体时间。'}


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

    now = datetime.now(timezone.utc).isoformat()
    store = container.store

    for dept in DEPARTMENTS:
        d = dict(dept)
        d.setdefault("admin_users", [])
        d.setdefault("agent_config", {"model": "deepseek-v4-flash", "temperature": 0.1, "max_tokens": 2048})
        d.setdefault("loop_phase", "human_in_loop")
        d.setdefault("review_stats", {"total": 0, "correct": 0, "accuracy": 0.0})
        d.setdefault("created_at", now)
        d["updated_at"] = now
        await store.upsert_department(d)
        print(f"[dept] {d['_id']} {d['name']}")

    for i, g in enumerate(GLOSSARY):
        entry = {
            "_id": f"glossary_seed_{i}",
            "canonical": g["canonical"],
            "synonyms": g["synonyms"],
            "dept_id": "",
            "created_by": "seed",
            "created_at": now,
        }
        await store.upsert_glossary(entry)
    print(f"[glossary] {len(GLOSSARY)} 条")

    await container.global_memory.set_calendar(CALENDAR)
    print("[calendar] 校历已写入全局记忆")

    await container.rule_engine.seed_defaults()
    await container.hook_engine.seed_defaults()
    print("[rules/hooks] 默认规则与钩子已种子化")
    created_skills = await seed_default_skills(store)
    print(f"[skills] 可执行基线 Skill 已就绪（本次新增 {created_skills}）")

    if container.mongo is not None:
        await container.mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
