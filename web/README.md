# 智能客服前端

我用 Next.js 与 React 提供客服问答和管理工作台。咨询端展示来源、会话与反馈；管理端组织业务组、文档审核、反馈 Loop 与策略实验。

```bash
npm ci
npm run dev
npm run build
```

开发默认端口3000，API由 next.config.mjs 代理到 BACKEND_URL（默认 http://localhost:8000）。完整 Compose 入口为 http://localhost:18080。演示账号及整体启动见根 README，页面说明见 ../docs/user-guide.md。
