# 运行与部署

## 当前运行状态

| 运行模式或能力 | 当前状态 |
| --- | --- |
| 本地内存模式 | 已完成界面访问、登录、少量真实模型问答与来源引用联调。启动器加载示例知识，数据随进程退出清空。 |
| 离线开发模式 | 可使用 hash 向量和规则降级检查路由、权限与引用流程；hash 向量不代表语义检索质量。 |
| 外部 Embedding / Reranker | 已提供配置与调用路径，当前客服场景尚未完成实际服务联调。 |
| MongoDB / Redis 持久化组合 | 已提供代码与配置，尚未完成完整组合的端到端运行验证。 |
| Docker Compose / Kubernetes / Helm | 提供部署配置与模板，完整容器启动、集群运行和扩缩容仍待验证。 |
| 订单、价格、退款和真伪识别 | 当前提供知识与流程咨询，真实业务操作及直接图片问答需另行接入。 |

上述状态不代表业务准确率、吞吐或延迟基准。模型服务、知识来源和部署环境不同，需要在目标环境重新检查。

## 本地开发

按根目录 [快速开始](../README.md#快速开始) 安装依赖，执行 `tools/init_env.py`，填写 `.env` 后运行 `tools/run_local.py`。启动器会启动 Web、FastAPI 与 pi，在同一后端进程内导入示例知识并消费异步任务。

| 服务 | 地址 |
| --- | --- |
| Web | http://127.0.0.1:18080 |
| FastAPI | http://127.0.0.1:18000/docs |
| pi | http://127.0.0.1:18100/health |

日志保存在 `_runtime/`；停止命令为 `python tools/run_local.py --stop`。此方式使用内存存储，重启后重新初始化。

## 配置

`tools/init_env.py` 会生成随机内部令牌和数据服务口令，并保留已有 `.env`。模型名称、服务地址和 Embedding 维度应按实际服务配置。

- `INTERNAL_API_TOKEN`：后端、Worker 和 pi 服务保持一致。
- `DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL`：聊天模型配置。
- `RELAY_API_KEY / RELAY_BASE_URL / EMBEDDING_MODEL / EMBEDDING_DIM`：向量与重排服务配置。
- `SEED_DEMO_USERS`：本地体验可启用；对外运行前关闭并移除已有演示账号。
- `CORS_ORIGINS`：按实际前端来源设置。

完整参数见 [环境样例](../.env.example)。

## Docker Compose

Compose 包含 MongoDB、Redis、backend、worker、pi-agent 和 web。启动、初始化与导入命令见根 README。Compose 内使用服务名通信；宿主机入口为 Web `18080`、API `18000`、pi `18100`、MongoDB `28017`、Redis `26379`。

先执行 `seed_data`，再执行 `ingest_department_files`；导入后重启 backend，使进程内索引从持久化文档重建。Windows 的 Next.js standalone 构建可能需要符号链接权限，可在目标 Linux 环境构建。

## 集群模板

配置位于 [deploy/k8s](../deploy/k8s) 和 [deploy/helm/shangzhi](../deploy/helm/shangzhi)。资源与监控指标统一使用 `shangzhi` 命名。部署前设置自有镜像、命名空间、Secret、PVC、Ingress 和业务组副本，并按目标存储和网络环境调整模板。

## 从早期预览版更新

`v0.1.1` 统一了业务组 ID、演示账号、数据库默认值、队列与监控指标名称。源码预览版不自动迁移旧数据库或队列；保留已有数据时需先备份，按新业务组映射迁移引用。不要把旧数据卷直接视为新配置的空白环境。

新咨询账号为 `customer / customer123`，商品组管理员为 `product_admin / admin123`。前端会使用新的本地令牌键，需要重新登录。
