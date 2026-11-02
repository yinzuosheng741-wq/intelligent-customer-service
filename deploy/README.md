# 集群部署模板

我为服务提供了 Kubernetes 与 Helm 模板，包含后端、pi、异步 Worker、数据服务、PVC、Ingress、监控和部门 Agent HPA。完整本地运行使用根目录 Compose。

模板路径：k8s/ 与 helm/wenshu/。Chart 路径与 wenshu_* 指标保留兼容标识；部署时请使用自己的镜像仓库、命名空间和Secret，并按业务组配置DEPT_ID。

目前集群配置作为部署示例，尚无本项目的集群性能或弹性伸缩实测结论。部署前必须在目标环境渲染、审核并验证资源配置。参见 ../docs/deployment.md。
