# FT-Agent 项目概览

**FT-Agent** - 财税智能 Agent 平台，支持多档位 Agent 服务、Token 计费系统和独立管理后台。

---

## 技术栈

### 后端 (ft-agent-backend)
| 类别 | 技术 |
|------|------|
| Web框架 | FastAPI + Uvicorn |
| 数据库 | PostgreSQL (生产) / SQLite (开发) |
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
| 路由 | Vue Router |
| HTTP | Axios |
| 构建 | Vite |

### 管理后台 (ft-agent-admin)
| 类别 | 技术 |
|------|------|
| 框架 | Vue 3 |
| UI库 | Element Plus |
| 状态管理 | Pinia |
| 路由 | Vue Router |
| HTTP | Axios |
| 构建 | Vite |

---

## 目录结构

```
FT-Agent/
├── ft-agent-backend/
│   ├── main.py              # FastAPI主入口
│   ├── core/
│   │   ├── engine.py        # Agent核心调度引擎
│   │   ├── rag_engine.py    # RAG知识库引擎
│   │   ├── database.py      # SQLAlchemy模型
│   │   ├── memory.py        # 记忆管理系统
│   │   └── security.py       # 安全工具
│   ├── routes/              # API路由
│   ├── services/            # 业务服务
│   └── tasks/              # 定时任务
├── ft-agent-frontend/       # 用户前端
├── ft-agent-admin/         # 管理后台
├── docs/
│   ├── DEPLOY.md           # 独立部署文档
│   ├── DEPLOY_DOCKER.md     # Docker部署文档
│   └── postgresql_schema.sql # 数据库表结构
└── docker-compose.yml      # Docker部署配置
```

---

## 已完成功能

### 用户前端 (ft-agent-frontend)
- [x] 用户注册/登录
- [x] 财税专家对话（基础版/专业版）
- [x] 会话记忆管理
- [x] 对话历史查看
- [x] Token 余额和充值
- [x] 订阅升级（升级赠送新等级1个月配额）
- [x] RAG知识库增强对话
- [x] 站内通知（铃铛+抽屉面板）
- [x] 好评差评反馈
- [x] 深色模式
- [x] 多语言（中文/英文）

### 管理后台 (ft-agent-admin)
- [x] 概览统计
- [x] 用户管理（启用/禁用、赠送Token）
- [x] Agent配置管理
- [x] 订阅版本管理（Tiers）
- [x] Token消耗统计
- [x] 对话分析统计
- [x] 知识库管理（RAG）
  - [x] PDF上传和索引
  - [x] 查看chunks预览
  - [x] RAG检索测试
  - [x] 导入/导出
- [x] 系统配置管理
- [x] 支付订单管理
- [x] 退款申请审核
- [x] 审计日志
- [x] 评价记录
- [x] 通知管理（发送/广播/删除）

### 后端 (ft-agent-backend)
- [x] 用户认证系统（JWT）
- [x] 多档位AI Agent（基础版/专业版）
- [x] Token计费系统
- [x] 订阅管理（定时过期检查）
- [x] RAG知识库增强
  - [x] PDF加载
  - [x] 智能chunking（按政策条目切分）
  - [x] 向量存储（Qdrant）
  - [x] 混合检索（向量+关键词）
  - [x] 参考资料注入Prompt
- [x] 会话记忆系统
- [x] Webhook服务（支付/注册事件）
- [x] Redis缓存（Token余额/会话/RAG）
- [x] API限流（GZip压缩/SQLite WAL优化）
- [x] 审计日志
- [x] 支付宝支付（沙箱）
- [x] 站内通知系统（前后端+管理后台）

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

## 启动方式

### 本地开发
```bash
# 后端
cd ft-agent-backend && python main.py

# 用户前端
cd ft-agent-frontend && npm run dev

# 管理后台
cd ft-agent-admin && npm run dev
```

### Docker部署
```bash
docker-compose up -d
```

### 独立部署
见 `docs/DEPLOY.md`

### 访问地址
| 服务 | 地址 |
|------|------|
| 用户前端 | http://localhost:3000 |
| 管理后台 | http://localhost:3001 |
| 后端API | http://localhost:8000/docs |
| 管理员账号 | admin / admin123 |

---

## 待办事项

### 高优先级
- [ ] 微信支付真实接入（配置 WECHAT_APP_ID / MCH_ID / API_KEY）
- [ ] 测试支付宝沙箱支付（生产需 ALIPAY_SANDBOX=false）

### 中等优先级
- [ ] 短信通知（集成短信网关）
- [ ] 订阅到期短信提醒

---

## 数据库清理（开发用）

```bash
cd ft-agent-backend
python script/clean_db.py
```

保留配置：admin_users, agents, user_tiers, system_configs