# 生产环境部署指南

## 目录
1. [环境准备](#环境准备)
2. [数据库配置](#数据库配置)
3. [应用部署](#应用部署)
4. [性能优化](#性能优化)
5. [监控与维护](#监控与维护)

---

## 环境准备

### 1. 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / 其他 Linux 发行版
- **Python**: 3.10+
- **内存**: 最小 2GB，推荐 4GB+
- **磁盘**: 最小 10GB，推荐 50GB+

### 2. 安装 Python 和依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install python310 python310-devel postgresql-server postgresql-contrib
```

---

## 数据库配置

### 方案 1: 本地 PostgreSQL

#### 1.1 安装 PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 1.2 创建数据库和用户

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 PostgreSQL 命令行中执行：
CREATE DATABASE agent_db;
CREATE USER agent_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE agent_db TO agent_user;

# 退出
\q
```

#### 1.3 配置远程访问（可选）

编辑 PostgreSQL 配置文件：

```bash
# 找到配置文件路径
sudo find /etc/postgresql -name postgresql.conf

# 编辑 postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# 修改以下行：
listen_addresses = '*'  # 监听所有IP（生产环境建议指定具体IP）
```

编辑访问控制文件：

```bash
# 编辑 pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# 添加以下行（允许本地网络访问）
host    agent_db    agent_user    0.0.0.0/0    md5
```

重启 PostgreSQL：

```bash
sudo systemctl restart postgresql
```

### 方案 2: 云数据库服务（推荐）

#### 阿里云 RDS
1. 登录阿里云控制台
2. 创建 RDS PostgreSQL 实例
3. 配置白名单（允许应用服务器IP访问）
4. 创建数据库和用户
5. 记录连接信息

#### 腾讯云 TencentDB
1. 登录腾讯云控制台
2. 创建 PostgreSQL 实例
3. 配置安全组
4. 创建数据库
5. 获取连接信息

---

## 应用部署

### 1. 克隆代码

```bash
# 创建应用目录
sudo mkdir -p /var/www/agent-backend
cd /var/www/agent-backend

# 上传代码（或使用 git clone）
# 假设已经上传到当前目录
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3.10 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制配置模板
cp .env.production.example .env

# 编辑配置
nano .env
```

配置示例：

```env
OPENAI_API_KEY=sk-your-deepseek-api-key
OPENAI_API_BASE=https://api.deepseek.com

HF_ENDPOINT=https://hf-mirror.com

# PostgreSQL 配置
DB_TYPE=postgresql
DB_USER=agent_user
DB_PASSWORD=your_strong_password
DB_HOST=localhost  # 或云数据库的地址
DB_PORT=5432
DB_NAME=agent_db
```

### 5. 初始化数据库

```bash
# 运行应用，会自动创建表
python main.py
```

看到 "✓ 数据库表初始化完成" 表示成功。

按 `Ctrl+C` 停止，然后继续配置生产服务器。

### 6. 使用 Gunicorn 部署（推荐）

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务（4个工作进程）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 7. 配置 Systemd 服务（自动启动）

创建服务文件：

```bash
sudo nano /etc/systemd/system/agent-backend.service
```

内容：

```ini
[Unit]
Description=Universal Agent Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/agent-backend
Environment="PATH=/var/www/agent-backend/venv/bin"
ExecStart=/var/www/agent-backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start agent-backend
sudo systemctl enable agent-backend
sudo systemctl status agent-backend
```

### 8. 配置 Nginx 反向代理（推荐）

安装 Nginx：

```bash
sudo apt install nginx
```

创建配置文件：

```bash
sudo nano /etc/nginx/sites-available/agent-backend
```

内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改为你的域名

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/agent-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. 配置 SSL（HTTPS）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书并自动配置 Nginx
sudo certbot --nginx -d your-domain.com
```

---

## 性能优化

### 1. 数据库优化

#### PostgreSQL 配置优化

编辑 `postgresql.conf`：

```conf
# 内存配置（根据服务器内存调整）
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
work_mem = 16MB

# 连接配置
max_connections = 100

# 性能配置
random_page_cost = 1.1  # SSD优化
```

#### 创建索引

```sql
-- 对话历史查询优化
CREATE INDEX idx_conv_user_time ON conversation_history(user_id, created_at DESC);

-- 用户记忆查询优化
CREATE INDEX idx_memory_user_key ON user_memory(user_id, key);
```

### 2. 应用优化

#### 增加工作进程

根据 CPU 核心数调整：

```bash
# 公式: 工作进程数 = (2 × CPU核心数) + 1
gunicorn main:app -w 8 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 启用缓存

考虑使用 Redis 缓存热数据：

```bash
# 安装 Redis
sudo apt install redis-server

# 在代码中集成 Redis 缓存（可选）
```

### 3. 向量数据库优化

如果使用 Qdrant，考虑：
- 独立部署 Qdrant 服务器
- 使用 SSD 存储
- 配置内存限制

---

## 监控与维护

### 1. 日志管理

#### 应用日志

配置日志轮转：

```bash
sudo nano /etc/logrotate.d/agent-backend
```

内容：

```
/var/log/agent-backend/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

#### 查看实时日志

```bash
# 查看服务日志
sudo journalctl -u agent-backend -f

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. 数据库备份

#### 自动备份脚本

创建备份脚本：

```bash
sudo nano /usr/local/bin/backup-db.sh
```

内容：

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/agent_db_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U agent_user -h localhost agent_db | gzip > $BACKUP_FILE

# 保留最近30天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

赋予执行权限：

```bash
sudo chmod +x /usr/local/bin/backup-db.sh
```

配置定时任务：

```bash
sudo crontab -e

# 添加每天凌晨2点备份
0 2 * * * /usr/local/bin/backup-db.sh
```

### 3. 性能监控

#### 使用 htop 监控资源

```bash
sudo apt install htop
htop
```

#### 监控数据库性能

```bash
# 连接到数据库
sudo -u postgres psql agent_db

# 查看活动连接
SELECT * FROM pg_stat_activity;

# 查看慢查询
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 4. 健康检查

创建健康检查端点（可选）：

在 `main.py` 中添加：

```python
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 安全建议

1. **防火墙配置**
   ```bash
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **限制数据库访问**
   - 只允许应用服务器IP访问数据库
   - 使用强密码
   - 定期更新密码

3. **使用 HTTPS**
   - 强制使用 SSL/TLS
   - 配置 HSTS

4. **定期更新**
   ```bash
   sudo apt update
   sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

---

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接信息（host, port, user, password）
   - 检查防火墙和安全组设置

2. **服务无法启动**
   - 查看日志：`sudo journalctl -u agent-backend -n 50`
   - 检查端口占用：`sudo netstat -tunlp | grep 8000`

3. **性能问题**
   - 检查数据库连接池
   - 增加工作进程数
   - 优化数据库索引

---

## 扩展性建议

### 水平扩展

1. **负载均衡**
   - 部署多个应用实例
   - 使用 Nginx 负载均衡

2. **数据库读写分离**
   - 配置主从复制
   - 读操作分发到从库

3. **使用消息队列**
   - 对于耗时任务，使用 Celery + Redis
   - 异步处理文档上传等操作

---

## 总结

完成以上步骤后，你的应用将：
- ✅ 使用 PostgreSQL 生产级数据库
- ✅ 通过 Systemd 自动启动
- ✅ 使用 Nginx 反向代理
- ✅ 支持 HTTPS 加密
- ✅ 配置自动备份
- ✅ 具备基础监控能力

**下一步建议**：
1. 配置日志收集（ELK Stack）
2. 设置监控告警（Prometheus + Grafana）
3. 实施 CI/CD 流程
4. 配置 CDN 加速静态资源
