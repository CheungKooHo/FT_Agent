# FT-Agent 管理后台

财税智能 Agent 平台的管理后台，基于 Vue 3 + Element Plus。

## 功能

- 概览统计
- 用户管理（启用/禁用、赠送 Token）
- 政策文档管理
- Token 消耗统计

## 快速开始

```bash
# 安装依赖
npm install

# 开发模式
npm run dev
```

访问 http://localhost:3001

## 项目结构

```
ft-agent-admin/
├── src/
│   ├── api/               # API 接口
│   ├── layouts/           # 布局组件
│   ├── router/            # 路由配置
│   ├── stores/            # 状态管理
│   └── views/             # 页面组件
├── index.html
├── vite.config.js
└── package.json
```

## 登录

默认管理员账号：
- 用户名: admin
- 密码: admin123
