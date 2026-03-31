# FT-Agent - 财税智能 Agent 平台

专业财税领域的 AI 智能助手平台，支持多档位 Agent 服务、Token 计费系统和独立管理后台。

## 项目组成

```
FT-Agent/
├── ft-agent-backend/     # 后端服务 (Python + FastAPI)
├── ft-agent-frontend/   # 用户前端 (Vue 3 + Element Plus)
├── ft-agent-admin/      # 管理后台 (Vue 3 + Element Plus)
├── start.sh             # 一键启动脚本 (Linux/Mac)
└── start.bat            # 一键启动脚本 (Windows)
```

## 快速开始

### 方法 1：一键启动（推荐）

**Linux/Mac**:
```bash
./start.sh
```

**Windows**:
```bash
start.bat
```

### 方法 2：手动启动

**终端 1 - 启动后端**:
```bash
cd ft-agent-backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pyjwt  # 如 requirements.txt 安装失败，补充安装此依赖
python init_data.py  # 初始化数据库
python main.py
```

**终端 2 - 启动用户前端**:
```bash
cd ft-agent-frontend
npm install
npm run dev
```

**终端 3 - 启动管理后台**:
```bash
cd ft-agent-admin
npm install
npm run dev
```

### 访问应用

- **用户前端**: http://localhost:3000
- **管理后台**: http://localhost:3001
- **后端 API**: http://localhost:8000/docs

## 功能特性

### 用户前端
- 用户注册/登录
- 财税专家对话（基础版/专业版）
- 会话记忆管理
- 对话历史查看
- Token 余额和充值
- 订阅升级

### 管理后台
- 概览统计
- 用户管理（启用/禁用、赠送 Token）
- 政策文档管理
- Token 消耗统计

### 后端功能
- 用户认证系统（JWT）
- 多档位 AI Agent（基础版/专业版）
- Token 计费系统
- 订阅管理
- 政策文档管理
- RAG 知识库增强
- 会话记忆系统

## 管理员账号

首次启动后，运行 `python init_data.py` 初始化数据库。

- **用户名**: admin
- **密码**: admin123

**请及时修改管理员密码！**

## 技术栈

| 层次 | 前端 | 管理后台 | 后端 |
|------|------|----------|------|
| 框架 | Vue 3 | Vue 3 | FastAPI |
| UI库 | Element Plus | Element Plus | - |
| 状态管理 | Pinia | Pinia | - |
| 路由 | Vue Router | Vue Router | - |
| HTTP | Axios | Axios | Uvicorn |
| 数据库 | - | - | SQLite/PostgreSQL |
| AI | - | - | LangChain + DeepSeek |

## 扩展开发

### Agent 定制

修改 `ft-agent-backend/core/tier_config.py` 中的 system prompt 来调整 Agent 行为。

### 政策知识库

通过管理后台上传政策文档，或调用 `/upload_policy` API 直接索引 PDF 文件。

## 许可证

MIT License
