# FT-Agent 财税智能平台部署文档

## 环境要求

- Node.js >= 18
- Python >= 3.10
- PostgreSQL >= 14
- Redis >= 6 (可选)

---

## 一、服务器配置

### 安装依赖 (Ubuntu/Debian)

```bash
apt update && apt upgrade -y
apt install -y python3.10 python3.10-venv python3-pip nodejs npm redis-server postgresql
```

### 创建数据库

```bash
# 方式一：如果 postgres 用户存在
sudo -u postgres psql

# 方式二：用 sudo 不支持的用户时，先切换到 postgres 用户
su - postgres -c "psql"

# 然后在 psql 里执行
CREATE DATABASE agent_db;
CREATE USER ft_agent WITH ENCRYPTED PASSWORD 'ft_agent123';
GRANT ALL PRIVILEGES ON DATABASE agent_db TO ft_agent;
\c agent_db
GRANT ALL ON SCHEMA public TO ft_agent;
\q
```

---

## 二、部署步骤

### 1. 下载代码

```bash
cd /www
git clone https://your-git-repo/FT-Agent.git ft-agent
cd ft-agent
```

### 2. 配置环境变量

```bash
cd ft-agent-backend
cp .env.example .env
nano .env
```

**.env 完整配置（按需修改）：**

```env
# ===== 数据库 =====
DB_TYPE=postgresql
DB_USER=ft_agent
DB_PASSWORD=ft_agent123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_db

# ===== AI 模型（必需）=====
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.deepseek.com
HF_ENDPOINT=https://hf-mirror.com

# ===== 支付宝支付 =====
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_SANDBOX=true
ALIPAY_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."（填写你的密钥）
ALIPAY_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."（填写你的密钥）

# ===== 微信支付（未配置可留空）=====
WECHAT_APP_ID=
WECHAT_MCH_ID=
WECHAT_API_KEY=

# ===== 支付回调地址 =====
PAYMENT_CALLBACK_URL=https://your-domain.com/payment/callback

# ===== 邮件服务（可选，暂未启用）=====
SMTP_ENABLED=false
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_email_password
SMTP_FROM_EMAIL=noreply@example.com

# ===== Redis 缓存（可选）=====
REDIS_URL=redis://localhost:6379

# ===== Webhook（可选）=====
WEBHOOK_ENABLED=false
WEBHOOK_URL=https://your-webhook.com/callback
```

> 注意：生产部署请确保 `ALIPAY_SANDBOX=false`，并填写真实的支付宝/微信支付密钥。

### 3. 初始化数据库

导入数据库表结构（使用项目中的 SQL 文件）：

```bash
psql -U ft_agent -d agent_db -h localhost -f sql/postgresql_schema.sql
```

### 4. 初始化后端

```bash
cd ft-agent-backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_data.py
```

### 4. 构建前端

```bash
cd ft-agent-frontend && npm install && npm run build
cd ../ft-agent-admin && npm install && npm run build
```

### 5. Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /www/ft-agent/ft-agent-frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /admin {
        alias /www/ft-agent/ft-agent-admin/dist;
        try_files $uri $uri/ /admin/index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

### 6. HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 7. Systemd 服务

```ini
[Unit]
Description=FT-Agent Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/www/ft-agent/ft-agent-backend
Environment="PATH=/www/ft-agent/ft-agent-backend/venv/bin"
ExecStart=/www/ft-agent/ft-agent-backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ft-agent-backend
sudo systemctl start ft-agent-backend
```

---

## 三、验证

```bash
curl http://localhost:8000/health
```

- 用户端: https://your-domain.com
- 管理后台: https://your-domain.com/admin

---

## 四、运维命令

```bash
# 查看日志
sudo journalctl -u ft-agent-backend -f

# 重启服务
sudo systemctl restart ft-agent-backend

# 备份数据库
pg_dump -U ft_agent agent_db > backup_$(date +%Y%m%d).sql

# 更新部署
cd /www/ft-agent && git pull
cd ft-agent-backend && source venv/bin/activate && pip install -r requirements.txt
cd ../ft-agent-frontend && npm run build && cd ../ft-agent-admin && npm run build
sudo systemctl restart ft-agent-backend
```