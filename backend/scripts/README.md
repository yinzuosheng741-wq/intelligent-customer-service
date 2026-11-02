# 运行与管理脚本

| 脚本 | 用途 |
|---|---|
| seed_data | 初始化7个业务组、术语、日历说明和默认策略 |
| ingest_department_files | 按目录映射业务组并导入示例知识 |
| seed_demo_data | 生成合成审核单、反馈与业务组 Skill（可选） |
| doctor | 以当前配置检查模型服务连接 |
| async_worker | 消费 Redis Stream 的入库和反馈任务 |
| migrate_memory | 将历史记忆结构转换为细粒度记忆 |

在 `backend` 目录执行 `python -m scripts.<name>`。持久化服务配置见根 `.env.example`。本地内存模式请使用根目录的 `tools/run_local.py`，由启动器在同一进程中完成知识初始化与问答服务装配。
