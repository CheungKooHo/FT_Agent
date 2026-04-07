# FT-Agent 财税智能平台 - 生产环境部署文档

## 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 服务器最低配置：2核4G

## 一、项目结构

```
FT-Agent/
├── docker-compose.yml          # Docker 编排配置
├── env.example                 # 环境变量示例
├── ft-agent-backend/          # 后端服务
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── ft-agent-frontend/         # 前端服务
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── docs/                      # 文档
```

## 二、部署步骤

### 1. 基础环境

SSH 登录服务器，创建项目目录：

```bash
mkdir -p /opt/ft-agent && cd /opt/ft-agent
```

### 2. 上传代码

方式一：Git 拉取
```bash
git clone <仓库地址> .
```

方式二：压缩包上传
```bash
scp ft-agent.tar.gz root@server:/opt/ft-agent/
tar -xzf ft-agent.tar.gz
```

### 3. 配置环境变量

```bash
cp env.example .env
nano .env
```

必填配置：
```env
# DeepSeek API Key（从 https://platform.deepseek.com 获取）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 数据库密码（务必修改为强密码）
DB_PASSWORD=YourStrongPassword123!

# API Base（可选，默认使用 DeepSeek）
OPENAI_API_BASE=https://api.deepseek.com
```

### 4. 拉取镜像并启动

```bash
# 拉取基础镜像（首次部署）
docker-compose pull

# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 5. 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend bash

# 初始化数据库表
python -c "from core.database import init_db; init_db()"

# 初始化默认数据
python init_data.py

# 退出容器
exit
```

### 6. 创建管理员账户

```bash
docker-compose exec backend python -c "
from core.database import SessionLocal, AdminUser
db = SessionLocal()
admin = AdminUser(
    username='admin',
    password_hash='admin123',  # 生产环境请修改默认密码！
    role='super_admin'
)
db.add(admin)
db.commit()
print('管理员账户已创建')
"
```

### 7. 验证部署

访问 `http://<服务器IP>` 检查前端是否正常。

API 健康检查：
```bash
curl http://localhost:8000/health
```

## 三、服务配置说明

### 端口映射

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| PostgreSQL | 5432 | 5432 | 数据库（仅内网访问）|
| Backend | 8000 | 8000 | API 服务 |
| Frontend | 80 | 80 | 前端页面 |

### 数据持久化

```yaml
# docker-compose.yml 中的 volume 配置
volumes:
  postgres_data:      # PostgreSQL 数据
  backend_uploads:    # 用户上传文件
  backend_qdrant:     # 向量数据库（如果有）
```

**重要**：生产环境务必配置数据备份策略！

### 环境变量

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| OPENAI_API_KEY | 是 | DeepSeek API Key | sk-xxx |
| OPENAI_API_BASE | 否 | API 地址，默认 deepseek | https://api.deepseek.com |
| DB_PASSWORD | 是 | PostgreSQL 密码 | 强密码 |
| HF_ENDPOINT | 否 | HuggingFace 镜像 | https://hf-mirror.com |

## 四、反向代理配置（Nginx）

如果需要通过域名访问，配合 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

配置 HTTPS：
```bash
# 安装 certbot
apt install certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d your-domain.com
```

## 五、维护命令

### 查看日志
```bash
# 后端日志
docker-compose logs -f backend

# 前端日志
docker-compose logs -f frontend

# 数据库日志
docker-compose logs -f postgres
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启后端
docker-compose restart backend

# 重启前端
docker-compose restart frontend
```

### 更新代码
```bash
cd /opt/ft-agent

# 拉取新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 备份数据库
```bash
# 备份
docker-compose exec postgres pg_dump -U agent_user agent_db > backup_$(date +%Y%m%d).sql

# 恢复
cat backup_20240101.sql | docker-compose exec -T postgres psql -U agent_user agent_db
```

### 清理日志
```bash
# 清理旧日志
docker-compose logs --tail=100 > recent.log

# 清理未使用的镜像
docker image prune -f
```

## 六、故障排查

### 1. 后端启动失败
```bash
# 查看后端详细日志
docker-compose logs backend

# 常见问题：
# - 数据库连接失败：检查 DB_PASSWORD 是否正确
# - 端口被占用：lsof -i:8000
```

### 2. 前端无法访问
```bash
# 检查 nginx 日志
docker-compose logs frontend

# 检查容器是否运行
docker-compose ps frontend
```

### 3. 数据库无法连接
```bash
# 检查 postgres 容器状态
docker-compose ps postgres

# 测试连接
docker-compose exec postgres pg_isready -U agent_user
```

### 4. 文件上传失败
```bash
# 检查 uploads 目录权限
docker-compose exec backend ls -la /app/uploads

# 修复权限
docker-compose exec backend chmod 777 /app/uploads
```

## 七、安全加固

1. **修改默认密码**
   ```bash
   # 修改管理员密码
   docker-compose exec backend python -c "
   from core.database import SessionLocal, AdminUser
   db = SessionLocal()
   admin = db.query(AdminUser).filter(AdminUser.username=='admin').first()
   admin.set_password('YourNewPassword')
   db.commit()
   "
   ```

2. **关闭数据库端口对外访问**
   ```yaml
   # docker-compose.yml 中 postgres 服务
   ports:
     - "127.0.0.1:5432:5432"  # 只允许本地访问
   ```

3. **配置防火墙**
   ```bash
   # 只开放必要端口
   ufw allow 80/tcp   # HTTP
   ufw allow 443/tcp  # HTTPS
   ufw allow 22/tcp   # SSH
   ufw enable
   ```

4. **定期更新**
   ```bash
   # 定期更新依赖
   docker-compose pull
   docker-compose up -d
   ```

## 八、性能优化

### 1. 增加后端资源
```yaml
# docker-compose.yml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

### 2. 配置 Redis 缓存（可选）
如需缓存，可添加 Redis 服务。

### 3. 数据库连接池
后端默认连接池已优化，如需调整修改 `core/database.py`。

## 九、联系方式

如有问题，请提交 Issue。
