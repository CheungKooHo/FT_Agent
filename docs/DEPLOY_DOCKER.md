# FT-Agent Docker 部署指南

## 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0

---

## 快速部署

### 1. 下载代码

```bash
cd /www
git clone https://your-git-repo/FT-Agent.git ft-agent
cd ft-agent
```

### 2. 配置环境变量

```bash
cp ft-agent-backend/env.example ft-agent-backend/.env
nano ft-agent-backend/.env
```

**必需配置项：**

```env
# AI 模型
OPENAI_API_KEY=your_openai_api_key

# 数据库密码
DB_PASSWORD=your_password

# 支付（按需配置）
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_PRIVATE_KEY=...
ALIPAY_PUBLIC_KEY=...
PAYMENT_CALLBACK_URL=https://your-domain.com/payment/callback
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看运行状态
docker-compose ps

# 查看后端日志
docker logs -f agent-backend

# 查看数据库日志
docker logs -f agent-postgres
```

### 4. 验证

```bash
curl http://localhost:8000/health
```

访问地址：
- 用户端: http://your-ip:3000
- 管理后台: http://your-ip:3001

---

## Docker 部署结构

| 容器 | 端口 | 说明 |
|------|------|------|
| agent-postgres | 5432 | PostgreSQL 数据库 |
| agent-backend | 8000 | 后端 API 服务 |
| agent-frontend | 3000 | 用户端前端 |
| agent-admin | 3001 | 管理后台前端 |

---

## 数据持久化

```yaml
volumes:
  postgres_data:      # PostgreSQL 数据
  backend_uploads:    # 用户上传文件
```

首次部署后数据会保存在 Docker volume 中，删除容器不会丢失。

---

## 更新部署

```bash
cd ft-agent

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 重启指定服务
docker-compose up -d --build backend
```

---

## 常用运维命令

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（慎用）
docker-compose down -v

# 进入后端容器
docker exec -it agent-backend /bin/bash

# 进入数据库
docker exec -it agent-postgres psql -U ft_agent -d agent_db

# 备份数据库
docker exec agent-postgres pg_dump -U ft_agent agent_db > backup_$(date +%Y%m%d).sql

# 查看资源使用
docker stats

# 查看所有容器日志
docker-compose logs -f
```

---

## 初始化数据库（可选）

如果需要手动导入 SQL 文件：

```bash
# 复制 SQL 文件到容器
docker cp sql/postgresql_schema.sql agent-postgres:/tmp/

# 执行 SQL
docker exec -i agent-postgres psql -U ft_agent -d agent_db < sql/postgresql_schema.sql
```

---

## 故障排查

**后端无法启动**
```bash
docker logs agent-backend
```

**数据库连接失败**
```bash
docker exec agent-postgres pg_isready -U ft_agent -d agent_db
```

**前端 502**
```bash
docker logs agent-frontend
curl http://localhost:8000/health
```

**清理重建**
```bash
docker-compose down -v
docker-compose up -d --build
```