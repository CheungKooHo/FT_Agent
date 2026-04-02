# FT-Agent 项目全面分析

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

### 基础设施
- **Docker**: docker-compose 部署 PostgreSQL + 后端 + 前端
- **端口**: 后端8000, 用户前端3000, 管理后台3001

---

## 目录结构

```
FT-Agent/
├── ft-agent-backend/
│   ├── main.py              # FastAPI主入口 (2164行)
│   ├── core/
│   │   ├── engine.py        # Agent核心调度引擎
│   │   ├── rag_engine.py    # RAG知识库引擎
│   │   ├── database.py      # SQLAlchemy模型
│   │   ├── memory.py        # 记忆管理系统
│   │   ├── tier_config.py   # 版本配置
│   │   └── security.py      # 安全工具
│   ├── agents/              # Agent处理器
│   ├── tools/              # 工具函数
│   ├── uploads/            # 上传文件
│   └── local_qdrant/       # Qdrant向量库
├── ft-agent-frontend/       # 用户前端
│   └── src/views/
│       ├── Chat.vue         # 对话页面
│       ├── Knowledge.vue    # 知识库页面
│       └── ...
├── ft-agent-admin/          # 管理后台
│   └── src/views/
│       ├── Knowledge.vue    # 知识库管理
│       ├── Agents.vue       # Agent配置
│       └── ...
└── docker-compose.yml       # Docker部署配置
```

---

## 数据库模型分析

### 核心表 (正在使用)
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

### 可能冗余的表
| 表名 | 用途 | 备注 |
|------|------|------|
| policy_documents | 政策文档 | ⚠️ 表存在但RAG用knowledge_files+向量库 |
| user_tier_relations | 用户-等级关联 | ⚠️ subscriptions已替代 |
| admin_users | 管理员 | ⚠️ 独立表，但后端只用一个admin账户 |
| system_configs | 系统配置 | ⚠️ 预留，未见使用 |

---

## API端点分析

### 用户端 (ft-agent-frontend 调用)
| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| /register | POST | 用户注册 | ✅ |
| /login | POST | 用户登录 | ✅ |
| /user/{user_id} | GET/PUT | 用户信息 | ✅ |
| /chat | POST | Agent对话 | ✅ |
| /memory | POST | 保存记忆 | ✅ |
| /memory/{user_id} | GET | 获取记忆 | ✅ |
| /memory | DELETE | 删除记忆 | ✅ |
| /conversation_history/{user_id} | GET | 对话历史 | ✅ |
| /conversation_history | DELETE | 清空历史 | ✅ |
| /upload_file | POST | 上传文件 | ✅ |
| /uploaded_files | GET | 列出已上传文件 | ⚠️ 与/knowledge/files重复 |
| /knowledge/files | GET | 知识库文件列表 | ✅ |
| /knowledge/files/{filename} | DELETE | 删除知识库文件 | ✅ |
| /knowledge/search_preview | GET | 检索预览 | ✅ |
| /knowledge/stats | GET | 知识库统计 | ✅ |
| /token/balance | GET | Token余额 | ✅ |
| /token/transactions | GET | Token流水 | ✅ |
| /token/recharge | POST | Token充值 | ✅ |
| /token/price | GET | Token价格 | ✅ |
| /subscription | GET | 订阅信息 | ✅ |
| /subscription/upgrade | POST | 升级订阅 | ✅ |
| /tiers | GET | 版本列表 | ✅ |

### 管理端 (ft-agent-admin 调用)
| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| /admin/login | POST | 管理员登录 | ✅ |
| /admin/stats/overview | GET | 概览统计 | ✅ |
| /admin/users | GET | 用户列表 | ✅ |
| /admin/users/{user_id}/toggle-status | PUT | 启用/禁用用户 | ✅ |
| /admin/users/{user_id}/grant-token | POST | 赠送Token | ✅ |
| /admin/stats/token-usage | GET | Token统计 | ✅ |
| /admin/agents | GET/POST | Agent列表/创建 | ✅ |
| /admin/agents/{agent_id} | PUT/DELETE | 更新/删除Agent | ✅ |
| /admin/tiers | GET/POST | 版本列表/创建 | ✅ |
| /admin/tiers/{tier_id} | PUT/DELETE | 更新/删除版本 | ✅ |
| /admin/policy-documents | GET/POST | 政策文档列表/创建 | ✅ |
| /admin/policy-documents/{doc_id} | PUT/DELETE | 更新/删除政策文档 | ✅ |
| /admin/system-configs | GET | 系统配置列表 | ✅ |
| /admin/system-configs/{key} | PUT | 更新系统配置 | ✅ |
| /admin/knowledge/files | GET/POST | 知识库文件列表/上传 | ✅ |
| /admin/knowledge/files/{filename} | DELETE | 删除知识库文件 | ✅ |
| /admin/knowledge/stats | GET | 知识库统计 | ✅ |
| /admin/knowledge/files/{filename}/chunks | GET | 获取文件chunks | ✅ |
| /admin/knowledge/search | GET | RAG检索测试 | ✅ |
| /admin/knowledge/export | GET | 导出知识库 | ✅ |
| /admin/knowledge/import | POST | 导入知识库 | ✅ |

### 已弃用/冗余端点
| 端点 | 状态 | 备注 |
|------|------|------|
| /upload_policy | ❌ 弃用 | 用/upload_file替代 |
| /uploaded_files | ⚠️ 冗余 | 与/knowledge/files功能重复 |

---

## 已完成功能

### 用户前端 (ft-agent-frontend)
- [x] 用户注册/登录
- [x] 财税专家对话（基础版/专业版）
- [x] 会话记忆管理
- [x] 对话历史查看
- [x] Token 余额和充值
- [x] 订阅升级
- [x] RAG知识库增强对话

### 管理后台 (ft-agent-admin)
- [x] 概览统计
- [x] 用户管理（启用/禁用、赠送Token）
- [x] Agent配置管理
- [x] 订阅版本管理（Tiers）
- [x] 政策文档管理
- [x] Token消耗统计
- [x] 知识库管理（RAG）
  - [x] 查看chunks预览
  - [x] RAG检索测试
  - [x] 导入/导出
  - [x] 批量上传

### 后端 (ft-agent-backend)
- [x] 用户认证系统（JWT）
- [x] 多档位AI Agent（基础版/专业版）
- [x] Token计费系统
- [x] 订阅管理
- [x] 政策文档管理
- [x] RAG知识库增强
  - [x] PDF加载
  - [x] 智能chunking（按政策条目切分）
  - [x] 向量存储（Qdrant）
  - [x] 混合检索（向量+关键词）
  - [x] 参考资料注入Prompt
- [x] 会话记忆系统

---

## 发现的问题

### 1. 冗余API端点
- `/uploaded_files` ✅ 已删除
- `/upload_policy` ✅ 已删除

### 2. 冗余数据库表
- `policy_documents` 表存在但RAG不直接使用（管理端Policies.vue仍使用）
- `user_tier_relations` 与 `subscriptions` 功能重复（部分死代码）

### 3. RAG知识库问题
**问题**: agent有时不按文件内容回答，或过度依赖文件

**现状**:
- RAG检索功能正常（向量化+关键词回退）
- Prompt已简化为基础模板
- 需要实际对话测试验证

### 4. Agent Prompt配置
- tier_config.py中hardcoded了默认prompt
- engine.py优先从数据库AgentConfig读取
- 数据库若无配置则用tier_config的默认值

---

## 已完成清理

- [x] 删除 `/upload_policy` 弃用端点
- [x] 删除前端未使用的 `getUploadedFiles` API

---

## 待办事项 (按优先级)

### 高优先级
- [ ] **测试RAG对话**: 验证agent能否正确使用检索结果回答

### 中优先级
- [ ] 清理 `UserTierRelation` 死代码
- [ ] PostgreSQL生产环境配置

### 低优先级
- [ ] 微信/钉钉集成
- [ ] 更详细的对话分析统计
- [ ] 多语言支持

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
