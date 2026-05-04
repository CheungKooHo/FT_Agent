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
sudo -u postgres psql

CREATE DATABASE agent_db;
CREATE USER agent_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE agent_db TO agent_user;
\c agent_db
GRANT ALL ON SCHEMA public TO agent_user;
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

**.env 必需配置：**

```env
DB_TYPE=postgresql
DB_USER=agent_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_db

OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.deepseek.com

ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_PRIVATE_KEY=your_private_key
ALIPAY_PUBLIC_KEY=your_public_key
WECHAT_APP_ID=your_wechat_app_id
WECHAT_MCH_ID=your_wechat_mch_id
WECHAT_API_KEY=your_wechat_api_key
PAYMENT_CALLBACK_URL=https://your-domain.com/payment/callback

SMTP_ENABLED=false
REDIS_URL=redis://localhost:6379
```

### 3. 初始化后端

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
pg_dump -U agent_user agent_db > backup_$(date +%Y%m%d).sql

# 更新部署
cd /www/ft-agent && git pull
cd ft-agent-backend && source venv/bin/activate && pip install -r requirements.txt
cd ../ft-agent-frontend && npm run build && cd ../ft-agent-admin && npm run build
sudo systemctl restart ft-agent-backend
```