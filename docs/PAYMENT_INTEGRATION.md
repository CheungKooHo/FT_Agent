# FT-Agent 支付对接文档

本文档详细介绍支付宝和微信支付的对接配置流程。

---

## 目录

1. [系统架构](#系统架构)
2. [支付流程](#支付流程)
3. [环境变量配置](#环境变量配置)
4. [支付宝对接](#支付宝对接)
5. [微信支付对接](#微信支付对接)
6. [回调地址配置](#回调地址配置)
7. [沙箱测试](#沙箱测试)
8. [生产部署](#生产部署)
9. [常见问题](#常见问题)

---

## 系统架构

### 支付相关服务

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   用户前端      │     │   后端 API      │     │   支付网关       │
│  ft-agent-     │────▶│  /payment/*    │────▶│  支付宝/微信     │
│  frontend      │     │                │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   PostgreSQL     │
                        │  payment_orders │
                        └─────────────────┘
```

### 数据库表

| 表名 | 用途 |
|------|------|
| `payment_orders` | 支付订单记录 |
| `token_accounts` | 用户Token余额 |
| `token_transactions` | Token流水明细 |

---

## 支付流程

### 整体时序

```
用户                    前端                    后端                    支付平台
 │                      │                       │                       │
 │──发起充值───────────▶│                       │                       │
 │                      │──创建订单───────────▶│                       │
 │                      │◀──返回二维码URL──────│                       │
 │◀──展示支付二维码─────────────────────────│                       │
 │                      │                       │                       │
 │──扫码支付───────────▶│                       │                       │
 │                      │                       │◀──回调通知───────────│
 │                      │                       │──验证签名───────────▶│
 │                      │                       │◀──验证结果──────────│
 │                      │                       │──更新订单状态────────│
 │◀──轮询订单状态───────│                       │                       │
```

### 订单状态流转

```
pending ──▶ paid ──▶ refunded
    │         │
    ▼         ▼
  failed    refunded
```

---

## 环境变量配置

### 基础配置

在 `ft-agent-backend/.env` 中配置以下环境变量：

```env
# 数据库密码
DB_PASSWORD=your_secure_password

# 支付回调地址（必须公网可访问）
PAYMENT_CALLBACK_URL=https://your-domain.com/payment/callback

# 支付宝应用配置
ALIPAY_APP_ID=2021000000000000
ALIPAY_PRIVATE_KEY=MIIEvQIBADANBgkqhkiG9w0BA...
ALIPAY_PUBLIC_KEY=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...
ALIPAY_SANDBOX=false

# 微信支付配置
WECHAT_APP_ID=wx0000000000000000
WECHAT_MCH_ID=0000000000
WECHAT_API_KEY=YourApiKeyHere32CharactersMin
WECHAT_SANDBOX=false
```

### 重要提醒

> **安全警告**
> - `.env` 文件包含敏感信息，**不要提交到 Git**
> - 生产环境务必使用复杂的数据库密码
> - 微信 API 密钥至少 32 位

---

## 支付宝对接

### 1. 创建应用

1. 登录 [支付宝开放平台](https://open.alipay.com/)
2. 进入「开发者中心」→ 「创建应用」
3. 选择「自研应用」→ 「网页/移动应用」
4. 填写应用信息

### 2. 获取配置

在应用详情页获取以下信息：

| 配置项 | 获取位置 | 说明 |
|--------|----------|------|
| `ALIPAY_APP_ID` | 应用信息 → APPID | 格式：16位数字 |
| `ALIPAY_PRIVATE_KEY` | 应用信息 → 开发设置 → 接口加签方式 | RSA2 密钥 |
| `ALIPAY_PUBLIC_KEY` | 支付宝密钥 | 支付宝公钥，用于验签 |

### 3. 生成密钥

#### 方式一：使用 OpenSSL 生成

```bash
# 1. 生成 RSA2 私钥（2048位）
openssl genrsa -out private_key.pem 2048

# 2. 转换为 PKCS8 格式（支付宝要求）
openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt \
  -in private_key.pem -out private_key_pkcs8.pem

# 3. 生成公钥
openssl rsa -in private_key.pem -pubout -out public_key.pem

# 4. 查看私钥（不含换行，用于环境变量）
cat private_key_pkcs8.pem | tr -d '\n'

# 5. 在支付宝后台「接口加签方式」上传公钥，获取支付宝公钥
```

#### 方式二：支付宝密钥工具

下载 [支付宝密钥生成工具](https://opendocs.alipay.com/open/291/106078)，图形化操作更方便。

### 4. 配置应用

1. 在支付宝后台「应用信息」→「开发设置」中：
   - 设置「接口加签方式」为 RSA2
   - 上传公钥
   - 获取支付宝公钥

2. 配置「支付能力」：
   - 当面付（扫码支付）
   - 手机网站支付（可选）

3. 设置「回调地址」：
   ```
   https://your-domain.com/payment/callback/alipay
   ```

### 5. 环境变量设置

```env
ALIPAY_APP_ID=2021000000000000
ALIPAY_PRIVATE_KEY=MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSj...
ALIPAY_PUBLIC_KEY=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
ALIPAY_SANDBOX=false
```

### 6. 密钥格式说明

私钥格式（用于 `ALIPAY_PRIVATE_KEY`）：
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----
```

公钥格式（用于 `ALIPAY_PUBLIC_KEY`）：
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
```

> **注意**：环境变量中的换行符需要替换为 `\n`：
> ```bash
> ALIPAY_PRIVATE_KEY=$(cat private_key.pem | tr -d '\n')
> ```

---

## 微信支付对接

### 1. 注册商户

1. 登录 [微信支付商户平台](https://pay.weixin.qq.com/)
2. 完成商户资质认证
3. 获取商户号（MCH_ID）

### 2. 获取配置

| 配置项 | 获取位置 | 说明 |
|--------|----------|------|
| `WECHAT_APP_ID` | 微信公众平台 → 开发设置 → AppID | 微信公众号或小程序 |
| `WECHAT_MCH_ID` | 商户平台 → 账户中心 → 商户信息 | 8-10位数字 |
| `WECHAT_API_KEY` | 商户平台 → 账户中心 → API安全 → API密钥 | 32位密钥 |

### 3. 获取 AppID

如果是公众号支付：
1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入「设置与开发」→「公众号设置」→「功能设置」
3. 获取 AppID

如果是小程序支付：
1. 登录 [微信小程序后台](https://mp.weixin.qq.com/)
2. 「开发」→「开发管理」→「开发设置」
3. 获取 AppID

### 4. 设置 API 密钥

1. 登录微信支付商户平台
2. 进入「账户中心」→「API安全」
3. 选择「API密钥」→「设置密钥」
4. 输入 32 位密钥（或点击「随机生成」）

### 5. 配置授权回调域

在微信公众平台后台设置：
1. 「设置与开发」→「公众号设置」→「功能设置」
2. 「JS接口安全域名」设置为你的域名
3. 「网页授权域名」设置为你的域名

### 6. 环境变量设置

```env
WECHAT_APP_ID=wx000000000000000000000000
WECHAT_MCH_ID=0000000000
WECHAT_API_KEY=Your32CharacterApiKeyHereXXXXX
WECHAT_SANDBOX=false
```

### 7. 微信支付类型

当前集成的是 **Native 支付（扫码支付）**，用户扫码后支付。

如需其他支付方式：
- JSAPI 支付（公众号内网页）
- H5 支付（手机浏览器）
- 小程序支付

需要额外配置和开发。

---

## 回调地址配置

### 回调 URL 要求

| 要求 | 说明 |
|------|------|
| 公网可访问 | 支付平台无法回调本地或内网地址 |
| HTTPS | 生产环境必须使用 HTTPS |
| 返回正确格式 | 必须返回特定格式的响应 |

### 回调地址

```
支付宝: https://your-domain.com/payment/callback/alipay
微信:   https://your-domain.com/payment/callback/wechat
```

### Nginx 配置示例

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 回调验证

支付平台回调会携带签名信息，后端会验证：

- **支付宝**：使用 RSA2 公钥验证签名
- **微信**：使用 API 密钥验证签名

如果签名验证失败，后端会拒绝处理回调。

---

## 沙箱测试

### 支付宝沙箱

1. 在支付宝开放平台创建应用时，可以选择「沙箱环境」
2. 设置 `ALIPAY_SANDBOX=true`
3. 使用沙箱环境的 APPID 和密钥

```env
ALIPAY_SANDBOX=true
ALIPAY_APP_ID=2021000000000000  # 沙箱APPID
```

沙箱网关地址会自动使用：`https://openapi.alipaydev.com/gateway.do`

### 微信支付沙箱

1. 在商户平台可以开启沙箱模式
2. 设置 `WECHAT_SANDBOX=true`
3. 获取沙箱环境的 API 密钥

```env
WECHAT_SANDBOX=true
WECHAT_MCH_ID=0000000000
WECHAT_API_KEY=your_sandbox_api_key
```

### 测试流程

1. 配置沙箱环境变量
2. 重启后端服务
3. 在前端发起支付
4. 使用沙箱支付工具完成模拟支付

---

## 生产部署

### 完整配置清单

```env
# ===================
# 基础配置
# ===================
DB_PASSWORD=your_very_secure_password_here
PAYMENT_CALLBACK_URL=https://your-production-domain.com/payment/callback

# ===================
# 支付宝配置
# ===================
ALIPAY_APP_ID=2021000000000000
ALIPAY_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANB...\n-----END PRIVATE KEY-----
ALIPAY_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\nMIIBIjANB...\n-----END PUBLIC KEY-----
ALIPAY_SANDBOX=false

# ===================
# 微信支付配置
# ===================
WECHAT_APP_ID=wx000000000000000000000000
WECHAT_MCH_ID=0000000000
WECHAT_API_KEY=Your32CharacterProductionApiKey
WECHAT_SANDBOX=false
```

### 部署检查清单

- [ ] 域名已备案并解析到服务器
- [ ] SSL 证书已配置
- [ ] Nginx 反向代理已配置
- [ ] 支付平台回调地址已设置
- [ ] 所有环境变量已正确配置
- [ ] 防火墙开放 80/443 端口
- [ ] 数据库密码已修改为强密码

### 支付平台配置

#### 支付宝

1. 应用已上线审核通过
2. 「当面付」能力已申请并审核通过
3. 回调地址已在支付宝后台配置
4. 公钥已正确配置

#### 微信支付

1. 商户资质已认证
2. Native 支付已开通
3. API 密钥已设置
4. 回调目录已配置

---

## 常见问题

### Q1: 支付成功但订单状态未更新

**原因**：回调地址配置错误或不可达

**排查**：
1. 检查 `PAYMENT_CALLBACK_URL` 是否公网可访问
2. 检查防火墙是否开放端口
3. 查看后端日志是否有回调记录
4. 确认回调地址格式正确

### Q2: 支付宝签名验证失败

**原因**：
1. 公钥/私钥不匹配
2. 支付宝公钥配置错误
3. 签名算法不匹配（RSA vs RSA2）

**排查**：
1. 确认使用的是 RSA2 签名
2. 确认公钥是支付宝提供的「支付宝公钥」而非「应用公钥」
3. 检查私钥格式是否正确（PKCS8）

### Q3: 微信支付签名验证失败

**原因**：
1. API 密钥错误
2. 签名算法不匹配

**排查**：
1. 确认 API 密钥完全正确
2. 检查签名计算是否使用 MD5/SHA256

### Q4: 沙箱支付无法使用

**原因**：生产环境变量覆盖了沙箱配置

**排查**：
1. 确认 `ALIPAY_SANDBOX=true` 或 `WECHAT_SANDBOX=true`
2. 确认使用的是沙箱环境的 APPID 和密钥
3. 检查环境变量是否正确加载

### Q5: 本地测试支付功能

**方案**：使用 Docker 本地部署完整环境

```bash
# 配置本地回调地址为穿透地址（如 ngrok）
PAYMENT_CALLBACK_URL=https://your-ngrok-url.io/payment/callback

# 或使用内网穿透工具
ngrok http 8000
```

### Q6: 订单重复处理

系统已实现幂等性：
- 同一订单号只处理一次
- 已完成的订单不会重复扣款
- 重复回调会被识别并忽略

### Q7: Token 未到账

**排查**：
1. 检查订单状态是否为 `paid`
2. 查看 `token_transactions` 表是否有记录
3. 检查 `token_accounts` 余额是否正确

---

## API 接口

### 创建支付订单

```
POST /api/payment/create
```

**请求**：
```json
{
  "order_type": "recharge",  // "recharge" 或 "subscription"
  "amount": 1000,             // 金额（分），1000 = 10元
  "token_amount": 200000,    // Token 数量
  "channel": "alipay"          // "alipay" 或 "wechat"
}
```

**响应**：
```json
{
  "status": "success",
  "order_id": "PAY17154000001234",
  "qr_code": "https://qr.alipay.com/xxx"
}
```

### 查询订单状态

```
GET /api/payment/status/{order_id}
```

**响应**：
```json
{
  "status": "success",
  "order_id": "PAY17154000001234",
  "status": "paid",           // "pending" / "paid" / "failed" / "refunded"
  "trade_no": "xxx",
  "paid_at": "2024-05-10T12:00:00"
}
```

### 关闭订单

```
POST /api/payment/close/{order_id}
```

**响应**：
```json
{
  "status": "success",
  "message": "订单已关闭"
}
```

---

## 技术细节

### 订单号生成规则

```
PAY{timestamp}{random}
示例：PAY1715400000123456
```

- `timestamp`: Unix 时间戳（秒）
- `random`: 4 位随机数

### Token 计算规则

```
Token数量 = 充值金额(元) / 每百万Token价格 × 1000000

默认价格：5元/百万Token
```

### 支付流程状态机

```
┌─────────┐    扫码支付    ┌─────────┐
│ pending │──────────────▶│ waiting │
└─────────┘               └─────────┘
     │                        │
     │ 取消/超时              │ 支付成功
     ▼                        ▼
┌─────────┐               ┌─────────┐
│ failed  │               │   paid  │
└─────────┘               └─────────┘
                                 │
                                 │ 退款
                                 ▼
                            ┌──────────┐
                            │ refunded │
                            └──────────┘
```