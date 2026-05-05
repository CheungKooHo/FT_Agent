-- FT-Agent 数据库表结构说明
-- PostgreSQL 生产环境使用

-- 用户表：存放注册用户基本信息
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) UNIQUE NOT NULL,          -- 用户唯一标识（UUID）
  username VARCHAR(255) UNIQUE NOT NULL,         -- 登录用户名
  password_hash VARCHAR(255) NOT NULL,           -- 密码 SHA256 哈希
  email VARCHAR(255) UNIQUE,                      -- 邮箱（可用于登录）
  phone VARCHAR(255) UNIQUE,                     -- 手机号
  nickname VARCHAR(255),                          -- 昵称
  avatar_url VARCHAR(255),                       -- 头像 URL
  bio TEXT,                                      -- 个人简介
  email_verified BOOLEAN DEFAULT FALSE,          -- 邮箱是否已验证
  email_verification_code VARCHAR(255),           -- 邮箱验证码
  is_active BOOLEAN DEFAULT TRUE,                -- 账号是否启用
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,-- 注册时间
  last_login TIMESTAMP                           -- 最后登录时间
);

-- 管理员表：admin 管理后台账号
CREATE TABLE admin_users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,         -- 管理员用户名
  password_hash VARCHAR(255) NOT NULL,           -- 密码哈希
  role VARCHAR(255) DEFAULT 'user_admin',        -- 角色：super_admin / user_admin / content_admin
  is_active BOOLEAN DEFAULT TRUE,                -- 是否启用
  last_login TIMESTAMP,                          -- 最后登录时间
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Agent 配置表：定义不同版本的财税助手
CREATE TABLE agents (
  id SERIAL PRIMARY KEY,
  agent_type VARCHAR(255) UNIQUE NOT NULL,       -- Agent 类型标识：tax_basic / tax_pro
  name VARCHAR(255) NOT NULL,                    -- 显示名称
  model VARCHAR(255) DEFAULT 'deepseek-chat',   -- 调用的 AI 模型
  prompt TEXT,                                   -- 系统提示词
  is_active BOOLEAN DEFAULT TRUE,                -- 是否启用
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话历史表：存放用户与 AI 的聊天记录（核心数据）
CREATE TABLE conversation_history (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,                 -- 用户 ID
  session_id VARCHAR(255),                       -- 会话 ID（同一 session 内的对话串联）
  agent_type VARCHAR(255),                       -- 使用的 Agent 类型
  role VARCHAR(255) NOT NULL,                    -- 消息角色：user / assistant
  content TEXT NOT NULL,                         -- 消息内容
  "references" TEXT,                             -- 引用的知识库文档（JSON 格式）
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户长期记忆表：AI 从对话中提取的长期记忆
CREATE TABLE user_memory (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,                 -- 用户 ID
  memory_type VARCHAR(255) NOT NULL,             -- 记忆类型：preference / fact / habit
  key VARCHAR(255) NOT NULL,                    -- 记忆键名
  value TEXT NOT NULL,                           -- 记忆值
  description TEXT,                              -- 描述
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订阅等级配置表：定义基础版/专业版的权益和价格
CREATE TABLE user_tiers (
  id SERIAL PRIMARY KEY,
  tier_code VARCHAR(255) UNIQUE NOT NULL,        -- 等级代码：basic / pro
  tier_name VARCHAR(255) NOT NULL,               -- 显示名称
  description TEXT,                              -- 等级说明
  features TEXT,                                 -- 功能列表（JSON 格式）
  monthly_token_quota INTEGER DEFAULT 1000,      -- 每月 Token 额度
  token_per_message INTEGER DEFAULT 50,           -- 每条消息消耗 Token
  price_monthly INTEGER DEFAULT 0,                -- 月费（分）
  agent_type VARCHAR(255),                      -- 关联的 Agent 类型
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token 账户表：用户 Token 余额
CREATE TABLE token_accounts (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) UNIQUE NOT NULL,         -- 用户 ID
  balance INTEGER DEFAULT 0,                     -- 当前剩余 Token
  total_purchased INTEGER DEFAULT 0,             -- 累计充值
  total_consumed INTEGER DEFAULT 0,              -- 累计消耗
  total_granted INTEGER DEFAULT 0,               -- 累计赠送
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token 交易记录表：Token 流水明细
CREATE TABLE token_transactions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  transaction_type VARCHAR(255) NOT NULL,        -- 类型：grant（赠送）/ purchase（购买）/ consume（消耗）/ refund（退款）
  amount INTEGER NOT NULL,                        -- 变动数量（正负）
  balance_after INTEGER NOT NULL,                -- 变动后余额
  description VARCHAR(255),                      -- 说明
  related_order_id VARCHAR(255),                 -- 关联订单号
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订阅表：用户订阅记录
CREATE TABLE subscriptions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  tier_id INTEGER NOT NULL,                      -- 关联 user_tiers.id
  status VARCHAR(255) NOT NULL,                  -- 状态：active / expired / cancelled
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP NOT NULL,
  auto_renew BOOLEAN DEFAULT FALSE,             -- 是否自动续费
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户-等级关联表：手动给用户分配等级（备用）
CREATE TABLE user_tier_relations (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  tier_id INTEGER NOT NULL,
  granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  granted_by VARCHAR(255)                       -- 授权者：system 或 admin username
);

-- 知识库文件表：用户上传的 PDF/TXT 文件
CREATE TABLE knowledge_files (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  filename VARCHAR(255) NOT NULL,              -- 系统存储文件名
  original_filename VARCHAR(255),               -- 用户原始文件名
  file_path VARCHAR(255),                      -- 文件存储路径
  file_size INTEGER DEFAULT 0,
  file_type VARCHAR(255) DEFAULT 'pdf',
  agent_type VARCHAR(255),                     -- 关联的 Agent 类型
  doc_id VARCHAR(255),                          -- 向量库文档 ID
  chunk_count INTEGER DEFAULT 0,               -- 切片数量
  is_indexed BOOLEAN DEFAULT FALSE,             -- 是否已索引到向量库
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知表：站内通知
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  notification_type VARCHAR(255) NOT NULL,      -- 类型：system / subscription / 其他
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表：管理员操作记录（安全审计）
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255),                        -- 操作人用户 ID
  username VARCHAR(255),                        -- 操作人用户名
  action VARCHAR(255) NOT NULL,                 -- 操作类型：login / logout / recharge / grant_token / update_config
  target_type VARCHAR(255),                     -- 操作对象类型：user / tier / agent / config
  target_id VARCHAR(255),                       -- 操作对象 ID
  details TEXT,                                 -- 详细信息（JSON）
  ip_address VARCHAR(255),
  user_agent VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话满意度评价表：用户对 AI 回复的好评/差评
CREATE TABLE message_feedback (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255) NOT NULL,
  message_index INTEGER NOT NULL,                -- 消息在会话中的索引
  rating VARCHAR(255) NOT NULL,                  -- rating：like / dislike
  reason VARCHAR(255),                           -- 差评原因
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 退款申请表：用户发起退款
CREATE TABLE refund_requests (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) NOT NULL,                -- 关联订单号
  user_id VARCHAR(255) NOT NULL,
  reason TEXT,                                  -- 退款原因
  status VARCHAR(255) DEFAULT 'pending',        -- 状态：pending / approved / rejected
  admin_id VARCHAR(255),                       -- 审核管理员
  admin_note TEXT,                              -- 管理员备注
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 支付订单表：充值/订阅订单
CREATE TABLE payment_orders (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) UNIQUE NOT NULL,         -- 内部订单号
  user_id VARCHAR(255) NOT NULL,
  order_type VARCHAR(255) NOT NULL,             -- 类型：recharge（充值）/ subscription（订阅）
  amount INTEGER NOT NULL,                      -- 金额（分）
  token_amount INTEGER NOT NULL,                 -- Token 数量
  payment_channel VARCHAR(255) NOT NULL,        -- 渠道：alipay / wechat
  status VARCHAR(255) DEFAULT 'pending',        -- 状态：pending / paid / failed / refunded
  trade_no VARCHAR(255),                        -- 第三方交易号
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  paid_at TIMESTAMP                             -- 支付时间
);

-- 系统配置表：键值对配置（网站名称、验证码等）
CREATE TABLE system_configs (
  id SERIAL PRIMARY KEY,
  key VARCHAR(255) UNIQUE NOT NULL,
  value TEXT,
  description VARCHAR(255),
  updated_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 初始化数据
-- ============================================================

INSERT INTO agents (agent_type, name, model, prompt, is_active) VALUES
('tax_basic', '财税专家-基础版', 'deepseek-chat',
 '你是一个专业的财税助手，帮助用户解答税务和财务相关问题。基础版提供基础的税务咨询服务。', TRUE),
('tax_pro', '财税专家-专业版', 'deepseek-chat',
 '你是一个专业的财税助手，帮助用户解答税务和财务相关问题。专业版提供更深入、更全面的税务筹划和咨询服务。', TRUE)
ON CONFLICT (agent_type) DO NOTHING;

INSERT INTO user_tiers (tier_code, tier_name, description, features, monthly_token_quota, token_per_message, price_monthly, agent_type) VALUES
('basic', '基础版', '适合个人用户的基础订阅', '["基础税务咨询", "知识库检索", "历史记录"]', 1000, 50, 0, 'tax_basic'),
('pro', '专业版', '适合企业用户的专业订阅', '["基础税务咨询", "知识库检索", "历史记录", "高级税务筹划", "优先响应"]', 5000, 30, 9900, 'tax_pro')
ON CONFLICT (tier_code) DO NOTHING;

INSERT INTO admin_users (username, password_hash, role) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'super_admin')
ON CONFLICT (username) DO NOTHING;