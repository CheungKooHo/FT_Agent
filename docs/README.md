# FT-Agent财税智能平台

**FT-Agent** - 财税智能 Agent 平台，支持多档位 Agent 服务、Token 计费系统和独立管理后台。

---

## 技术栈

### 后端 (ft-agent-backend)
| 类别 | 技术 |
|------|------|
| Web框架 | FastAPI + Uvicorn |
| 数据库 | PostgreSQL |
| AI/LLM | LangChain + DeepSeek (openai兼容API) |
| 文档处理 | PyPDF |
| 向量数据库 | Qdrant |
| Embeddings | HuggingFace (paraphrase-multilingual-MiniLM-L12-v2) |
| 认证 | PyJWT |
| Token计数 | tiktoken |

### 前端 (ft-agent-frontend - 用户端)
| 类别 | 技术 |
|------|------|
| 框架 | Vue 3 |
| UI库 | Element Plus |
| 状态管理 | Pinia |
| 路由 | Vue Router (History模式) |
| HTTP | Axios |
| 构建 | Vite |

### 管理后台 (ft-agent-admin)
| 类别 | 技术 |
|------|------|
| 框架 | Vue 3 |
| UI库 | Element Plus |
| 状态管理 | Pinia |
| 路由 | Vue Router (History模式，base: /admin/) |
| HTTP | Axios |
| 构建 | Vite |

---

## 快速开始

### 本地开发

```bash
# 后端
cd ft-agent-backend && source venv/bin/activate && python main.py

# 用户前端
cd ft-agent-frontend && npm run dev

# 管理后台
cd ft-agent-admin && npm run dev
```

### 或使用一键启动脚本

```bash
./start.sh
```

### Docker

```bash
docker-compose up -d
```

---

## 已完成功能

### 用户前端
- [x] 用户注册/登录
- [x] 财税专家对话（基础版/专业版）
- [x] 会话记忆管理
- [x] 对话历史查看
- [x] Token 余额和充值
- [x] 订阅升级
- [x] RAG知识库增强对话
- [x] 站内通知
- [x] 好评差评反馈
- [x] 深色模式
- [x] 多语言（中文/英文）

### 管理后台
- [x] 概览统计
- [x] 用户管理（启用/禁用、赠送Token）
- [x] Agent配置管理
- [x] 订阅版本管理
- [x] Token消耗统计
- [x] 对话分析统计
- [x] 知识库管理（RAG）
- [x] 系统配置管理
- [x] 支付订单管理
- [x] 退款申请审核
- [x] 审计日志
- [x] 评价记录
- [x] 通知管理

### 后端
- [x] 用户认证系统（JWT）
- [x] 多档位AI Agent
- [x] Token计费系统
- [x] 订阅管理
- [x] RAG知识库
- [x] 会话记忆系统
- [x] API限流
- [x] 审计日志
- [x] 支付宝/微信支付
- [x] 站内通知系统

---

## 数据库模型

| 表名 | 用途 |
|------|------|
| users | 用户信息 |
| admin_users | 管理员账号 |
| agents | Agent配置 |
| conversation_history | 对话历史 |
| user_memory | 用户长期记忆 |
| user_tiers | 订阅等级配置 |
| token_accounts | Token账户余额 |
| token_transactions | Token流水明细 |
| subscriptions | 用户订阅记录 |
| user_tier_relations | 用户-等级关联 |
| knowledge_files | 知识库文件 |
| notifications | 站内通知 |
| audit_logs | 审计日志 |
| message_feedback | 对话评价 |
| refund_requests | 退款申请 |
| payment_orders | 支付订单 |
| system_configs | 系统配置 |

---

## 文档

- [部署文档](./DEPLOY.md) - 服务器部署详细指南
- [Docker部署](./DEPLOY_DOCKER.md) - Docker 部署指南
- [支付对接](./PAYMENT_INTEGRATION.md) - 支付宝/微信支付配置

---

## 访问地址

| 服务 | 地址 |
|------|------|
| 用户前端 | http://localhost:3000 |
| 管理后台 | http://localhost:3001 |
| 后端 API | http://localhost:8000/docs |
| 管理员账号 | admin / admin123 |

---

## 待办事项

### 高优先级
- [ ] 微信支付真实接入
- [ ] 测试支付宝沙箱支付

### 中等优先级
- [ ] 短信通知
- [ ] 订阅到期短信提醒