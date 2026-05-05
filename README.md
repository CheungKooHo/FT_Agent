# FT-Agent - 财税智能 Agent 平台

专业财税领域的 AI 智能助手平台，支持多档位 Agent 服务、Token 计费系统和独立管理后台。

## 项目组成

```
FT-Agent/
├── ft-agent-backend/     # 后端服务 (Python + FastAPI)
├── ft-agent-frontend/    # 用户前端 (Vue 3 + Element Plus)
├── ft-agent-admin/       # 管理后台 (Vue 3 + Element Plus)
├── docs/                  # 部署文档
├── docker-compose.yml     # Docker 部署配置
└── sql/                   # 数据库 SQL 文件
```

## 快速开始

### 本地开发

**后端**:
```bash
cd ft-agent-backend
python main.py
```

**用户前端**:
```bash
cd ft-agent-frontend
npm run dev
```

**管理后台**:
```bash
cd ft-agent-admin
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

详见 [docs/DEPLOY.md](docs/DEPLOY.md) 和 [docs/DEPLOY_DOCKER.md](docs/DEPLOY_DOCKER.md)

### 访问应用

| 服务 | 地址 |
|------|------|
| 用户前端 | http://localhost:3000 |
| 管理后台 | http://localhost:3001 |
| 后端 API | http://localhost:8000/docs |

## 功能特性

### 用户前端
- 用户注册/登录
- 财税专家对话（基础版/专业版）
- 会话记忆管理
- 对话历史查看
- Token 余额和充值
- 订阅升级
- RAG 知识库增强对话
- 站内通知
- 好评差评反馈
- 深色模式 / 多语言

### 管理后台
- 概览统计
- 用户管理（启用/禁用、赠送 Token）
- Agent 配置管理
- 订阅版本管理
- Token 消耗统计
- 对话分析统计
- 知识库管理（RAG）
- 系统配置管理
- 支付订单管理
- 退款申请审核
- 审计日志
- 通知管理（发送/广播）

### 后端功能
- 用户认证系统（JWT）
- 多档位 AI Agent（基础版/专业版）
- Token 计费系统
- 订阅管理
- RAG 知识库增强
- 会话记忆系统
- Webhook 服务
- Redis 缓存
- API 限流
- 审计日志
- 支付宝支付（沙箱）
- 站内通知系统

## 管理员账号

- **用户名**: admin
- **密码**: admin123

## 数据库

本地开发使用 SQLite，生产环境使用 PostgreSQL。

初始化数据库：
```bash
psql -U ft_agent -d agent_db -f sql/postgresql_schema.sql
```

详见 [docs/DEPLOY.md](docs/DEPLOY.md#数据库初始化)

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | PostgreSQL / SQLite |
| AI/LLM | LangChain + DeepSeek |
| 向量数据库 | Qdrant |
| 前端框架 | Vue 3 + Element Plus |
| 状态管理 | Pinia |
| 构建工具 | Vite |

## 扩展开发

### Agent 定制

修改 `ft-agent-backend/core/tier_config.py` 中的 system prompt 来调整 Agent 行为。

### 知识库管理

通过管理后台上传 PDF 文档，系统会自动 chunking 和索引。

## 部署文档

- [独立部署](docs/DEPLOY.md)
- [Docker 部署](docs/DEPLOY_DOCKER.md)
- [项目概览](docs/TODO.md)

## 许可证

MIT License