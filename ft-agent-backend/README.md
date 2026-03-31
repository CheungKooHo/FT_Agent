# FT-Agent 后端服务

财税智能 Agent 平台的后端服务，基于 FastAPI 构建。

## 功能

- 用户认证系统（JWT）
- 多档位 AI Agent（基础版/专业版）
- Token 计费系统
- 订阅管理
- 政策文档管理
- RAG 知识库增强
- 会话记忆系统

## 启动

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库（首次）
python init_data.py

# 启动服务
python main.py
```

## API 文档

启动服务后访问: http://localhost:8000/docs

## 初始化

运行 `python init_data.py` 将创建：
- Tier 配置（基础版、专业版）
- 管理员账户（admin/admin123）
- 系统配置

## 目录结构

```
├── main.py              # 应用入口
├── init_data.py          # 数据库初始化
├── requirements.txt      # 依赖
├── core/
│   ├── config.py         # 配置
│   ├── database.py       # 数据库模型
│   ├── engine.py         # Agent 引擎
│   ├── memory.py         # 记忆管理
│   ├── rag_engine.py     # RAG 检索
│   ├── security.py       # JWT 认证
│   └── tier_config.py    # Tier 配置
├── agents/               # Agent 配置
├── tasks/                # 定时任务
└── venv/                 # 虚拟环境
```
