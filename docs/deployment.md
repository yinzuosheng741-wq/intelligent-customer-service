# 运行与部署

我使用 Docker Compose 组织 MongoDB、Redis、backend、worker、pi-agent 和 web。完整启动步骤见根 README。

## 配置

执行 python tools/init_env.py 生成本地 .env；填写模型与向量服务密钥，并根据提供方配置模型名称。内部 API 的 INTERNAL_API_TOKEN 必须在后端与 pi 服务一致。生产环境关闭演示用户、设置明确 CORS 和正式认证信息。

本地入口为 web:18080、backend:18000、pi:18100，MongoDB:28017、Redis:26379。服务间保持 Compose 内部端口。

## 文档与索引

先执行 seed_data，再执行 ingest_department_files；脚本独立进程入库后重启 backend，便于进程内索引重建。Mongo 向量配置用于共享存储；内存模式适合单进程测试，不提供进程间数据共享。

## 集群模板

deploy/k8s 和 deploy/helm/wenshu 提供部署示例。部署前设置自有镜像地址、namespace、Secret、PVC、Ingress 和业务组副本；模板中兼容资源标识不代表已完成集群验收。不要直接应用占位密钥。

Windows 的 Next.js standalone 产物可能遇到符号链接权限问题；建议在目标 Linux 容器环境构建并验收。当前本地检查不等于容器部署或HPA性能结论。
