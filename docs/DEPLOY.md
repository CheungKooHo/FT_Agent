# FT-Agent 财税智能平台部署文档

## 环境要求

- Node.js >= 18
- Python >= 3.10
- PostgreSQL >= 14
- Nginx

---

##目录

1. [项目结构](#项目结构)
2. [服务器部署](#服务器部署)
3. [Docker部署](#docker部署)
4. [Nginx配置](#nginx配置)
5. [支付对接](#支付对接)
6. [运维命令](#运维命令)

---

## 项目结构

```
FT-Agent/
├── ft-agent-backend/ # FastAPI 后端
├── ft-agent-frontend/   # 用户前端 (Vue 3)
├── ft-agent-admin/       # 管理后台 (Vue 3)
├── docs/                 # 文档
├── sql/                  # 数据库 SQL
├── docker-compose.yml    # Docker 部署配置
└── start.sh              # 本地一键启动脚本
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 用户前端 | http://localhost:3000 |
| 管理后台 | http://localhost:3001 |
| 后端 API | http://localhost:8000/docs |
| 管理员账号 | admin / admin123 |

---

## 服务器部署

### 1. 服务器初始化

```bash
# 更新系统
apt update && apt upgrade -y

# 安装依赖
apt install -y python3.10 python3.10-venv python3-pip nodejs npm postgresql nginx

# 安装 Node.js 20（如需要）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt install -y nodejs
```

### 2. 配置 PostgreSQL 数据库

```bash
sudo -u postgres psql

# 在 psql 中执行
CREATE DATABASE agent_db;
CREATE USER ft_agent WITH ENCRYPTED PASSWORD 'ft_agent123';
GRANT ALL PRIVILEGES ON DATABASE agent_db TO ft_agent;
\c agent_db
GRANT ALL ON SCHEMA public TO ft_agent;
ALTER DATABASE agent_db OWNER TO ft_agent;
\q
```

### 3. 拉取代码

```bash
cd /home
git clone https://github.com/CheungKooHo/FT-Agent.git FT_Agent
cd FT_Agent
```

### 4. 配置后端环境变量

```bash
cd ft-agent-backend
cp .env.example .env
nano .env
```

**必需配置：**

```env
# ===== 数据库 =====
DB_TYPE=postgresql
DB_USER=ft_agent
DB_PASSWORD=ft_agent123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_db

# ===== JWT 密钥（生产环境务必修改）=====
JWT_SECRET_KEY=your-secret-key-here-change-in-production

# ===== AI 模型（必需）=====
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.deepseek.com
HF_ENDPOINT=https://hf-mirror.com

# ===== 支付回调地址 ======
PAYMENT_CALLBACK_URL=https://your-domain.com/payment/callback

# ===== 支付宝支付 =====
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
ALIPAY_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...
ALIPAY_SANDBOX=false

# ===== 微信支付 =====
WECHAT_APP_ID=wx000000000000000000000000
WECHAT_MCH_ID=0000000000
WECHAT_API_KEY=YourApiKeyHere32CharactersMin
WECHAT_SANDBOX=false
```

### 5. 安装后端依赖

```bash
cd ft-agent-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyjwt bcrypt
python init_data.py
```

### 6. 构建前端

```bash
# 用户前端
cd ft-agent-frontend
npm install
npm run build

# 管理后台
cd ft-agent-admin
npm install
npm run build
```

### 7. Nginx 配置

```bash
nano /etc/nginx/sites-enabled/default
```

**完整配置：**

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /home/FT_Agent/ft-agent-frontend/dist;
    index index.html;

    server_name _;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /admin {
        alias /home/FT_Agent/ft-agent-admin/dist;
        try_files $uri $uri/ /admin/index.html;
        sub_filter '/assets/' '/admin/assets/';
        sub_filter_once off;
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

```bash
nginx -t && systemctl reload nginx
```

### 8. Systemd 服务（推荐）

```bash
nano /etc/systemd/system/ft-agent-backend.service
```

内容：

```ini
[Unit]
Description=FT-Agent Backend
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory=/home/FT_Agent/ft-agent-backend
Environment="PATH=/home/FT_Agent/ft-agent-backend/venv/bin"
Environment="JWT_SECRET_KEY=your-jwt-secret-key"
Environment="DB_PASSWORD=ft_agent123"
ExecStart=/home/FT_Agent/ft-agent-backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable ft-agent-backend
systemctl start ft-agent-backend
```

### 9. HTTPS（可选，有域名时）

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

---

## Docker部署

### 快速启动

```bash
cd FT_Agent
cp ft-agent-backend/.env.example ft-agent-backend/.env
nano ft-agent-backend/.env  # 配置必要的环境变量
docker-compose up -d
```

### 验证

```bash
curl http://localhost:8000/health
```

### 容器端口

| 容器 | 端口 | 说明 |
|------|------|------|
| agent-postgres | 5432 | PostgreSQL |
| agent-backend | 8000 | 后端 API |
| agent-frontend | 3000 | 用户前端 |
| agent-admin | 3001 | 管理后台 |

### 更新部署

```bash
git pull
docker-compose up -d --build
```

---

## Nginx 配置说明

### 前端路由（History模式）

用户前端和管理后台都使用 Vue Router History 模式：

- 用户前端：`/` 下所有路由 → `try_files $uri $uri/ /index.html`
- 管理后台：`/admin/` 下所有路由 → `try_files $uri $uri/ /admin/index.html`

### admin 子目录的特殊处理

管理后台构建时资源路径为 `/admin/assets/...`，但 Vue 组件内的 import 路径可能是 `/assets/...`。使用 `sub_filter` 替换 HTML 中的路径。

如果 build 时配置了 `base: '/admin/'`（推荐），则不需要 sub_filter。

### API代理

`/api/*` 请求代理到后端 `http://127.0.0.1:8000/*`，后端通过中间件去掉 `/api` 前缀。

---

## 支付对接

详细文档见 [PAYMENT_INTEGRATION.md](./PAYMENT_INTEGRATION.md)

### 快速配置

**支付宝：**
1. 登录 [支付宝开放平台](https://open.alipay.com/)
2. 创建应用，获取 APP_ID
3. 生成 RSA2 密钥对
4. 配置 `.env` 中的 `ALIPAY_APP_ID`、`ALIPAY_PRIVATE_KEY`、`ALIPAY_PUBLIC_KEY`

**微信支付：**
1. 登录 [微信支付商户平台](https://pay.weixin.qq.com/)
2. 获取商户号（MCH_ID）
3. 设置 API 密钥（32位）
4. 配置 `.env` 中的 `WECHAT_APP_ID`、`WECHAT_MCH_ID`、`WECHAT_API_KEY`

### 回调地址

```
支付宝: https://your-domain.com/payment/callback/alipay
微信:   https://your-domain.com/payment/callback/wechat
```

---

## 运维命令

### 后端管理

```bash
# 查看状态
systemctl status ft-agent-backend

# 查看日志
journalctl -u ft-agent-backend -f

# 重启服务
systemctl restart ft-agent-backend

# 进入后端容器（Docker）
docker exec -it agent-backend /bin/bash
```

### 数据库

```bash
# 备份
pg_dump -U ft_agent agent_db > backup_$(date +%Y%m%d).sql

# 进入数据库
psql -U ft_agent -d agent_db -h localhost

# Docker 进入
docker exec -it agent-postgres psql -U ft_agent -d agent_db
```

### 日志

```bash
# 后端日志
tail -f /home/FT_Agent/ft-agent-backend/backend.log

# Nginx 错误日志
tail -f /var/log/nginx/error.log

# Nginx 访问日志
tail -f /var/log/nginx/access.log
```

### 更新部署

```bash
cd /home/FT_Agent
git pull origin master

# 后端
cd ft-agent-backend && source venv/bin/activate && pip install -r requirements.txt

# 前端
cd ft-agent-frontend && npm run build
cd ft-agent-admin && npm run build

# 重启
systemctl restart ft-agent-backend
```

---

## 故障排查

### 500错误

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 查看后端日志
journalctl -u ft-agent-backend -n 50
```

### 502 错误

```bash
# 后端未启动或连接失败
systemctl status ft-agent-backend
curl http://localhost:8000/health
```

### 白屏问题（Admin）

1. 检查浏览器 F12 Console 错误
2. 检查 `/admin/assets/` 路径是否正确
3. 如果是路径问题，rebuild 前端：
   ```bash
   cd ft-agent-admin && npm run build
   ```

### 数据库连接失败

```bash
# 检查 PostgreSQL
sudo -u postgres pg_isready -U ft_agent -d agent_db
systemctl status postgresql
```