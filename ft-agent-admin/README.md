# FT-Agent 管理后台

财税智能 Agent 平台的管理后台，基于 Vue 3 + Element Plus。

## 功能

- 概览统计
- 用户管理（启用/禁用、赠送 Token）
- Agent 配置管理
- 订阅版本管理（Tiers）
- Token 消耗统计
- 对话分析统计
- 知识库管理（RAG）
  - PDF 上传和索引
  - 查看 chunks 预览
  - RAG 检索测试
  - 导入/导出
- 系统配置管理
- 支付订单管理
- 退款申请审核
- 审计日志
- 评价记录
- 通知管理（发送/广播/删除）

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
│   ├── stores/            # 状态管理 (Pinia)
│   └── views/             # 页面组件
├── index.html
├── vite.config.js
└── package.json
```

## 登录

默认管理员账号：
- 用户名: admin
- 密码: admin123

## 配置

创建 `.env.local`：
```env
VITE_API_BASE_URL=http://localhost:8000
```