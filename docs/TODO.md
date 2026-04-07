# FT-Agent 项目概览

## 项目概述

**FT-Agent** - 财税智能 Agent 平台，支持多档位 Agent 服务、Token 计费系统和独立管理后台。

---

## 技术栈

### 后端 (ft-agent-backend)
| 类别 | 技术 |
|------|------|
| Web框架 | FastAPI + Uvicorn |
| 数据库 | SQLite (本地) / PostgreSQL (Docker) |
| AI/LLM | LangChain + DeepSeek (openai兼容API) |
| 文档处理 | PyPDF |
| 向量数据库 | Qdrant (本地文件存储) |
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
│   │   ├── tier_config.py   # 版本配置
│   │   └── security.py      # 安全工具
│   ├── script/
│   │   ├── clean_db.py      # 数据库清理脚本
│   │   ├── migrate_db.py     # 数据库迁移脚本
│   │   └── download_model.py # 模型下载脚本
│   ├── uploads/             # 上传文件临时目录
│   └── local_qdrant/       # Qdrant向量库
├── ft-agent-frontend/       # 用户前端
├── ft-agent-admin/          # 管理后台
├── docs/
│   ├── TODO.md             # 项目概览
│   └── deploy-production.md # 部署文档
└── docker-compose.yml       # Docker部署配置
```

---

## 数据库模型

| 表名 | 用途 | 状态 |
|------|------|------|
| users | 用户信息 | ✅ 正常使用 |
| token_accounts | Token账户 | ✅ 正常使用 |
| token_transactions | Token流水 | ✅ 正常使用 |
| subscriptions | 用户订阅 | ✅ 正常使用 |
| user_tiers | 订阅版本定义 | ✅ 正常使用 |
| agents | Agent配置 | ✅ 正常使用 |
| knowledge_files | 知识库文件 | ✅ 正常使用 |
| conversation_history | 对话历史 | ✅ 正常使用 |
| user_memory | 用户记忆 | ✅ 正常使用 |
| admin_users | 管理员 | ✅ 正常使用 |
| system_configs | 系统配置 | ✅ 正常使用 |

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

### 后端 (ft-agent-backend)
- [x] 用户认证系统（JWT）
- [x] 多档位AI Agent（基础版/专业版）
- [x] Token计费系统
- [x] 订阅管理
- [x] RAG知识库增强
  - [x] PDF加载
  - [x] 智能chunking（按政策条目切分）
  - [x] 向量存储（Qdrant）
  - [x] 混合检索（向量+关键词）
  - [x] 参考资料注入Prompt
- [x] 会话记忆系统

---

## Token配置

| 版本 | 每月配额 | 每条消息消耗 |
|------|---------|-------------|
| 基础版 | 1,000,000 | 50 |
| 专业版 | 5,000,000 | 100 |

- 新用户注册赠送：基础版1个月配额（1,000,000）
- 升级（基础→专业）：赠送专业版1个月配额（5,000,000）
- 降级：Token余额保持不变

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

### 访问地址
- 用户前端: http://localhost:3000
- 管理后台: http://localhost:3001
- 后端API: http://localhost:8000/docs
- 管理员账号: admin / admin123

---

## 数据库清理

```bash
cd ft-agent-backend
python script/clean_db.py
```

清理内容：users, token_accounts, token_transactions, subscriptions, conversation_history, user_memory, knowledge_files

保留配置：admin_users, agents, user_tiers, system_configs
