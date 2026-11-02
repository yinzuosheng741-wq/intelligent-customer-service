# 集群部署模板

此目录提供 Kubernetes 与 Helm 模板，包含后端、pi、异步 Worker、数据服务、PVC、Ingress、监控及业务组 Agent HPA。

- `k8s/`：独立资源示例。
- `helm/shangzhi/`：参数化 Helm Chart。
- 命名空间、资源前缀与监控指标统一使用 `shangzhi`。

模板需要填写自有镜像、Secret、存储与域名，并按业务组设置 `DEPT_ID`。集群运行与扩缩容尚待验证；运行状态和配置要求统一见 [部署说明](../docs/deployment.md#当前运行状态)。
