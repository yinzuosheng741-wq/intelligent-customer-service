# 负载测试

我保留了部门 Agent 的 k6 压测脚本，用于在相同模型配额、数据集和资源条件下对比不同副本数。

```bash
k6 run --summary-export one.json department-agent.js
k6 run --summary-export twenty.json department-agent.js
python compare_results.py one.json twenty.json
```

先按脚本要求设置目标URL、登录信息与业务组，再记录有效吞吐、错误率和P95；模型侧TPM/RPM、共享存储和跨部门合并都会影响结果。当前仓库未发布经过验证的吞吐或延迟数字。
