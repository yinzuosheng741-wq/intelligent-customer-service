# 电商客服业务设计

我按资料责任划分七个知识组，将商品、价格、退款、物流、鉴定、理赔和图像材料知识分别管理。跨业务问题通过路由和混合检索组合证据。

| 内部 ID | 业务组 |
|---|---|
| dept_product | 商品识别与检索组 |
| dept_pricing | 比价导购组 |
| dept_refund | 退款服务组 |
| dept_logistics | 订单物流组 |
| dept_authentication | 二手鉴定组 |
| dept_claims | 售后理赔组 |
| dept_evidence | 图像材料支持组 |

内部 ID 和 customer/admin 角色是协议标识，前端展示业务名称。scenario/departments.json 和 glossary.json 是配置快照，运行时由 backend/scripts/seed_data.py 写入；变更时需同步配置快照与种子数据。

## 专业能力与策略

23项能力目录包括5项视觉处理、3项信息检索、15项业务操作需求。目录中的 knowledge_only_not_registered 表示用于解释业务知识，尚未注册成可执行接口。

默认可执行策略包括图像材料补充、售后理赔导航和时效核验。策略使用既有 SkillExecutor 执行查询扩展、top-k 调整和模板指令，并保留版本、分组及 outcome。

## 文档接入

正式使用时，应按知识组上传商品说明、品牌鉴定标准、带时间和规格的价格记录及适用平台售后规则，再经过审核和版本治理。当前示例是开发用流程知识，不能作为商家承诺或平台政策。来源口径见 knowledge-sources.md。
