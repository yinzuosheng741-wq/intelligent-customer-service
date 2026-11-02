# 管理与验证脚本

| 脚本 | 用途 |
|---|---|
| seed_data | 初始化7个业务组、术语、日历说明和默认策略 |
| ingest_department_files | 按目录映射业务组并导入示例知识 |
| seed_demo_data | 生成合成审核单、反馈与业务组 Skill（可选） |
| doctor | 以当前配置检查模型服务连接 |
| async_worker | 消费 Redis Stream 的入库和反馈任务 |
| evaluate_rag | 文件级 Hit Rate@5、MRR、引用与答案关键点检查 |
| migrate_memory | 将历史记忆结构转换为细粒度记忆 |

在 backend 目录执行 python -m scripts.<name>。持久化服务配置见根 .env.example。内存模式的种子与问答需要在同一进程内完成，可使用 tools/verify_scenario.py 检查。
