# FT-Agent 后端服务

财税智能 Agent 平台的后端服务，基于 FastAPI 构建。

## 功能

- 用户认证系统（JWT）
- 多档位 AI Agent（基础版/专业版）
- Token 计费系统
- 订阅管理
- RAG 知识库增强（PDF 上传、chunking、向量检索）
- 会话记忆系统
- Webhook 服务（支付/注册事件）
- Redis 缓存
- API 限流（GZip 压缩、SQLite WAL 优化）
- 审计日志
- 支付宝支付（沙箱）
- 站内通知系统

## 启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

API 文档：http://localhost:8000/docs

## 数据库

本地开发使用 SQLite，生产环境使用 PostgreSQL。

配置 `.env`：
```env
DB_TYPE=sqlite  # 开发环境
DB_TYPE=postgresql  # 生产环境
DB_USER=ft_agent
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_db
```

初始化数据库：
```bash
psql -U ft_agent -d agent_db -f ../sql/postgresql_schema.sql
```

## 环境变量

复制 `env.example` 为 `.env` 并配置：

```env
# AI 模型
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.deepseek.com

# 数据库
DB_TYPE=sqlite

# 支付（可选）
ALIPAY_APP_ID=your_app_id
ALIPAY_SANDBOX=true
```

完整配置见 `env.example`。

## 目录结构

```
ft-agent-backend/
├── main.py              # 应用入口
├── init_data.py         # 数据初始化
├── requirements.txt     # 依赖
├── env.example          # 环境变量模板
├── core/
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库模型
│   ├── engine.py        # Agent 引擎
│   ├── memory.py        # 记忆管理
│   ├── rag_engine.py    # RAG 检索
│   └── security.py      # JWT 认证
├── routes/              # API 路由
├── services/            # 业务服务
├── tasks/               # 定时任务
├── script/              # 开发工具脚本
└── uploads/            # 用户上传文件
```

## 开发工具

```bash
# 清理数据库（保留配置）
python script/clean_db.py

# 预下载 embedding 模型
python script/download_model.py
```