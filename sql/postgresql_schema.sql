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
  prompt TEXT,                                    -- 系统提示词
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
  content TEXT NOT NULL,                          -- 消息内容
  "references" TEXT,                               -- 引用的知识库文档（JSON 格式）
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户长期记忆表：AI 从对话中提取的长期记忆
CREATE TABLE user_memory (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,                 -- 用户 ID
  memory_type VARCHAR(255) NOT NULL,              -- 记忆类型：preference / fact / habit
  key VARCHAR(255) NOT NULL,                      -- 记忆键名
  value TEXT NOT NULL,                             -- 记忆值
  description TEXT,                                -- 描述
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订阅等级配置表：定义基础版/专业版的权益和价格
CREATE TABLE user_tiers (
  id SERIAL PRIMARY KEY,
  tier_code VARCHAR(255) UNIQUE NOT NULL,         -- 等级代码：basic / pro
  tier_name VARCHAR(255) NOT NULL,                -- 显示名称
  description TEXT,                                -- 等级说明
  features TEXT,                                   -- 功能列表（JSON 格式）
  monthly_token_quota INTEGER DEFAULT 1000,       -- 每月 Token 额度
  token_per_message INTEGER DEFAULT 50,            -- 每条消息消耗 Token
  price_monthly INTEGER DEFAULT 0,                 -- 月费（分）
  agent_type VARCHAR(255),                        -- 关联的 Agent 类型
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token 账户表：用户 Token 余额
CREATE TABLE token_accounts (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) UNIQUE NOT NULL,           -- 用户 ID
  balance INTEGER DEFAULT 0,                       -- 当前剩余 Token
  total_purchased INTEGER DEFAULT 0,               -- 累计充值
  total_consumed INTEGER DEFAULT 0,                -- 累计消耗
  total_granted INTEGER DEFAULT 0,                 -- 累计赠送
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token 交易记录表：Token 流水明细
CREATE TABLE token_transactions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  transaction_type VARCHAR(255) NOT NULL,         -- 类型：grant（赠送）/ purchase（购买）/ consume（消耗）/ refund（退款）
  amount INTEGER NOT NULL,                           -- 变动数量（正数增加，负数减少）
  balance_after INTEGER NOT NULL,                   -- 变动后余额
  description VARCHAR(255),                         -- 说明
  related_order_id VARCHAR(255),                    -- 关联订单号
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订阅表：用户订阅记录
CREATE TABLE subscriptions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  tier_id INTEGER NOT NULL,                          -- 关联 user_tiers.id
  status VARCHAR(255) NOT NULL,                     -- 状态：active / expired / cancelled
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP NOT NULL,
  auto_renew BOOLEAN DEFAULT FALSE,                 -- 是否自动续费
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户-等级关联表：手动给用户分配等级（备用）
CREATE TABLE user_tier_relations (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  tier_id INTEGER NOT NULL,
  granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  granted_by VARCHAR(255)                           -- 授权者：system 或 admin username
);

-- 知识库文件表：用户上传的 PDF/TXT 文件
CREATE TABLE knowledge_files (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  filename VARCHAR(255) NOT NULL,                  -- 系统存储文件名
  original_filename VARCHAR(255),                   -- 用户原始文件名
  file_path VARCHAR(255),                           -- 文件存储路径
  file_size INTEGER DEFAULT 0,                      -- 文件大小（字节）
  file_type VARCHAR(255) DEFAULT 'pdf',             -- 文件类型：pdf / txt / doc
  agent_type VARCHAR(255),                          -- 关联的 Agent 类型
  doc_id VARCHAR(255),                              -- 向量库文档 ID
  chunk_count INTEGER DEFAULT 0,                    -- 切片数量
  is_indexed BOOLEAN DEFAULT FALSE,                 -- 是否已索引到向量库
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知表：站内通知
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  notification_type VARCHAR(255) NOT NULL,          -- 类型：system / subscription / 其他
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表：管理员操作记录（安全审计）
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255),                             -- 操作人用户 ID
  username VARCHAR(255),                            -- 操作人用户名
  action VARCHAR(255) NOT NULL,                      -- 操作类型：login / logout / recharge / grant_token / update_config
  target_type VARCHAR(255),                         -- 操作对象类型：user / tier / agent / config
  target_id VARCHAR(255),                          -- 操作对象 ID
  details TEXT,                                      -- 详细信息（JSON 格式）
  ip_address VARCHAR(255),                          -- 操作人 IP 地址
  user_agent VARCHAR(255),                          -- 浏览器 User-Agent
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话满意度评价表：用户对 AI 回复的好评/差评
CREATE TABLE message_feedback (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255) NOT NULL,
  message_index INTEGER NOT NULL,                    -- 消息在会话中的索引
  rating VARCHAR(255) NOT NULL,                     -- 评分：like / dislike
  reason VARCHAR(255),                              -- 差评原因
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 退款申请表：用户发起退款
CREATE TABLE refund_requests (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) NOT NULL,                   -- 关联订单号
  user_id VARCHAR(255) NOT NULL,
  reason TEXT,                                      -- 退款原因
  status VARCHAR(255) DEFAULT 'pending',            -- 状态：pending / approved / rejected
  admin_id VARCHAR(255),                            -- 审核管理员
  admin_note TEXT,                                  -- 管理员备注
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 支付订单表：充值/订阅订单
CREATE TABLE payment_orders (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) UNIQUE NOT NULL,            -- 内部订单号
  user_id VARCHAR(255) NOT NULL,
  order_type VARCHAR(255) NOT NULL,                 -- 类型：recharge（充值）/ subscription（订阅）
  amount INTEGER NOT NULL,                           -- 金额（分）
  token_amount INTEGER NOT NULL,                     -- Token 数量
  payment_channel VARCHAR(255) NOT NULL,            -- 渠道：alipay / wechat
  status VARCHAR(255) DEFAULT 'pending',            -- 状态：pending / paid / failed / refunded
  trade_no VARCHAR(255),                            -- 第三方交易号
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  paid_at TIMESTAMP                                 -- 支付时间
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
-- 所有列添加注释
-- ============================================================

COMMENT ON TABLE users IS '用户表：存放注册用户基本信息';
COMMENT ON COLUMN users.id IS '自增主键';
COMMENT ON COLUMN users.user_id IS '用户唯一标识（UUID）';
COMMENT ON COLUMN users.username IS '登录用户名';
COMMENT ON COLUMN users.password_hash IS '密码 SHA256 哈希';
COMMENT ON COLUMN users.email IS '邮箱（可用于登录）';
COMMENT ON COLUMN users.phone IS '手机号';
COMMENT ON COLUMN users.nickname IS '昵称';
COMMENT ON COLUMN users.avatar_url IS '头像 URL';
COMMENT ON COLUMN users.bio IS '个人简介';
COMMENT ON COLUMN users.email_verified IS '邮箱是否已验证';
COMMENT ON COLUMN users.email_verification_code IS '邮箱验证码';
COMMENT ON COLUMN users.is_active IS '账号是否启用';
COMMENT ON COLUMN users.created_at IS '注册时间';
COMMENT ON COLUMN users.last_login IS '最后登录时间';

COMMENT ON TABLE admin_users IS '管理员表：admin 管理后台账号';
COMMENT ON COLUMN admin_users.id IS '自增主键';
COMMENT ON COLUMN admin_users.username IS '管理员用户名';
COMMENT ON COLUMN admin_users.password_hash IS '密码哈希';
COMMENT ON COLUMN admin_users.role IS '角色：super_admin / user_admin / content_admin';
COMMENT ON COLUMN admin_users.is_active IS '是否启用';
COMMENT ON COLUMN admin_users.last_login IS '最后登录时间';
COMMENT ON COLUMN admin_users.created_at IS '创建时间';

COMMENT ON TABLE agents IS 'AI Agent 配置表：定义不同版本的财税助手';
COMMENT ON COLUMN agents.id IS '自增主键';
COMMENT ON COLUMN agents.agent_type IS 'Agent 类型标识：tax_basic / tax_pro';
COMMENT ON COLUMN agents.name IS '显示名称';
COMMENT ON COLUMN agents.model IS '调用的 AI 模型';
COMMENT ON COLUMN agents.prompt IS '系统提示词';
COMMENT ON COLUMN agents.is_active IS '是否启用';
COMMENT ON COLUMN agents.created_at IS '创建时间';
COMMENT ON COLUMN agents.updated_at IS '更新时间';

COMMENT ON TABLE conversation_history IS '对话历史表：存放用户与 AI 的聊天记录（核心数据）';
COMMENT ON COLUMN conversation_history.id IS '自增主键';
COMMENT ON COLUMN conversation_history.user_id IS '用户 ID';
COMMENT ON COLUMN conversation_history.session_id IS '会话 ID（同一 session 内的对话串联）';
COMMENT ON COLUMN conversation_history.agent_type IS '使用的 Agent 类型';
COMMENT ON COLUMN conversation_history.role IS '消息角色：user / assistant';
COMMENT ON COLUMN conversation_history.content IS '消息内容';
COMMENT ON COLUMN conversation_history.references IS '引用的知识库文档（JSON 格式）';
COMMENT ON COLUMN conversation_history.created_at IS '创建时间';

COMMENT ON TABLE user_memory IS '用户长期记忆表：AI 从对话中提取的长期记忆';
COMMENT ON COLUMN user_memory.id IS '自增主键';
COMMENT ON COLUMN user_memory.user_id IS '用户 ID';
COMMENT ON COLUMN user_memory.memory_type IS '记忆类型：preference / fact / habit';
COMMENT ON COLUMN user_memory.key IS '记忆键名';
COMMENT ON COLUMN user_memory.value IS '记忆值';
COMMENT ON COLUMN user_memory.description IS '描述';
COMMENT ON COLUMN user_memory.created_at IS '创建时间';
COMMENT ON COLUMN user_memory.updated_at IS '更新时间';

COMMENT ON TABLE user_tiers IS '订阅等级配置表：定义基础版/专业版的权益和价格';
COMMENT ON COLUMN user_tiers.id IS '自增主键';
COMMENT ON COLUMN user_tiers.tier_code IS '等级代码：basic / pro';
COMMENT ON COLUMN user_tiers.tier_name IS '显示名称';
COMMENT ON COLUMN user_tiers.description IS '等级说明';
COMMENT ON COLUMN user_tiers.features IS '功能列表（JSON 格式）';
COMMENT ON COLUMN user_tiers.monthly_token_quota IS '每月 Token 额度';
COMMENT ON COLUMN user_tiers.token_per_message IS '每条消息消耗 Token';
COMMENT ON COLUMN user_tiers.price_monthly IS '月费（分）';
COMMENT ON COLUMN user_tiers.agent_type IS '关联的 Agent 类型';
COMMENT ON COLUMN user_tiers.is_active IS '是否启用';
COMMENT ON COLUMN user_tiers.created_at IS '创建时间';
COMMENT ON COLUMN user_tiers.updated_at IS '更新时间';

COMMENT ON TABLE token_accounts IS 'Token 账户表：用户 Token 余额';
COMMENT ON COLUMN token_accounts.id IS '自增主键';
COMMENT ON COLUMN token_accounts.user_id IS '用户 ID';
COMMENT ON COLUMN token_accounts.balance IS '当前剩余 Token';
COMMENT ON COLUMN token_accounts.total_purchased IS '累计充值';
COMMENT ON COLUMN token_accounts.total_consumed IS '累计消耗';
COMMENT ON COLUMN token_accounts.total_granted IS '累计赠送';
COMMENT ON COLUMN token_accounts.created_at IS '创建时间';
COMMENT ON COLUMN token_accounts.updated_at IS '更新时间';

COMMENT ON TABLE token_transactions IS 'Token 交易记录表：Token 流水明细';
COMMENT ON COLUMN token_transactions.id IS '自增主键';
COMMENT ON COLUMN token_transactions.user_id IS '用户 ID';
COMMENT ON COLUMN token_transactions.transaction_type IS '类型：grant（赠送）/ purchase（购买）/ consume（消耗）/ refund（退款）';
COMMENT ON COLUMN token_transactions.amount IS '变动数量（正数增加，负数减少）';
COMMENT ON COLUMN token_transactions.balance_after IS '变动后余额';
COMMENT ON COLUMN token_transactions.description IS '说明';
COMMENT ON COLUMN token_transactions.related_order_id IS '关联订单号';
COMMENT ON COLUMN token_transactions.created_at IS '创建时间';

COMMENT ON TABLE subscriptions IS '订阅表：用户订阅记录';
COMMENT ON COLUMN subscriptions.id IS '自增主键';
COMMENT ON COLUMN subscriptions.user_id IS '用户 ID';
COMMENT ON COLUMN subscriptions.tier_id IS '关联 user_tiers.id';
COMMENT ON COLUMN subscriptions.status IS '状态：active / expired / cancelled';
COMMENT ON COLUMN subscriptions.start_date IS '订阅开始时间';
COMMENT ON COLUMN subscriptions.end_date IS '订阅到期时间';
COMMENT ON COLUMN subscriptions.auto_renew IS '是否自动续费';
COMMENT ON COLUMN subscriptions.created_at IS '创建时间';
COMMENT ON COLUMN subscriptions.updated_at IS '更新时间';

COMMENT ON TABLE user_tier_relations IS '用户-等级关联表：手动给用户分配等级（备用）';
COMMENT ON COLUMN user_tier_relations.id IS '自增主键';
COMMENT ON COLUMN user_tier_relations.user_id IS '用户 ID';
COMMENT ON COLUMN user_tier_relations.tier_id IS '等级 ID';
COMMENT ON COLUMN user_tier_relations.granted_at IS '授权时间';
COMMENT ON COLUMN user_tier_relations.granted_by IS '授权者：system 或 admin username';

COMMENT ON TABLE knowledge_files IS '知识库文件表：用户上传的 PDF/TXT 文件';
COMMENT ON COLUMN knowledge_files.id IS '自增主键';
COMMENT ON COLUMN knowledge_files.user_id IS '用户 ID';
COMMENT ON COLUMN knowledge_files.filename IS '系统存储文件名';
COMMENT ON COLUMN knowledge_files.original_filename IS '用户原始文件名';
COMMENT ON COLUMN knowledge_files.file_path IS '文件存储路径';
COMMENT ON COLUMN knowledge_files.file_size IS '文件大小（字节）';
COMMENT ON COLUMN knowledge_files.file_type IS '文件类型：pdf / txt / doc';
COMMENT ON COLUMN knowledge_files.agent_type IS '关联的 Agent 类型';
COMMENT ON COLUMN knowledge_files.doc_id IS '向量库文档 ID';
COMMENT ON COLUMN knowledge_files.chunk_count IS '切片数量';
COMMENT ON COLUMN knowledge_files.is_indexed IS '是否已索引到向量库';
COMMENT ON COLUMN knowledge_files.created_at IS '上传时间';

COMMENT ON TABLE notifications IS '通知表：站内通知';
COMMENT ON COLUMN notifications.id IS '自增主键';
COMMENT ON COLUMN notifications.user_id IS '用户 ID';
COMMENT ON COLUMN notifications.notification_type IS '类型：system / subscription / 其他';
COMMENT ON COLUMN notifications.title IS '通知标题';
COMMENT ON COLUMN notifications.content IS '通知内容';
COMMENT ON COLUMN notifications.is_read IS '是否已读';
COMMENT ON COLUMN notifications.created_at IS '创建时间';

COMMENT ON TABLE audit_logs IS '审计日志表：管理员操作记录（安全审计）';
COMMENT ON COLUMN audit_logs.id IS '自增主键';
COMMENT ON COLUMN audit_logs.user_id IS '操作人用户 ID';
COMMENT ON COLUMN audit_logs.username IS '操作人用户名';
COMMENT ON COLUMN audit_logs.action IS '操作类型：login / logout / recharge / grant_token / update_config';
COMMENT ON COLUMN audit_logs.target_type IS '操作对象类型：user / tier / agent / config';
COMMENT ON COLUMN audit_logs.target_id IS '操作对象 ID';
COMMENT ON COLUMN audit_logs.details IS '详细信息（JSON 格式）';
COMMENT ON COLUMN audit_logs.ip_address IS '操作人 IP 地址';
COMMENT ON COLUMN audit_logs.user_agent IS '浏览器 User-Agent';
COMMENT ON COLUMN audit_logs.created_at IS '操作时间';

COMMENT ON TABLE message_feedback IS '对话满意度评价表：用户对 AI 回复的好评/差评';
COMMENT ON COLUMN message_feedback.id IS '自增主键';
COMMENT ON COLUMN message_feedback.user_id IS '用户 ID';
COMMENT ON COLUMN message_feedback.session_id IS '会话 ID';
COMMENT ON COLUMN message_feedback.message_index IS '消息在会话中的索引';
COMMENT ON COLUMN message_feedback.rating IS '评分：like / dislike';
COMMENT ON COLUMN message_feedback.reason IS '差评原因';
COMMENT ON COLUMN message_feedback.created_at IS '评价时间';

COMMENT ON TABLE refund_requests IS '退款申请表：用户发起退款';
COMMENT ON COLUMN refund_requests.id IS '自增主键';
COMMENT ON COLUMN refund_requests.order_id IS '关联订单号';
COMMENT ON COLUMN refund_requests.user_id IS '申请人用户 ID';
COMMENT ON COLUMN refund_requests.reason IS '退款原因';
COMMENT ON COLUMN refund_requests.status IS '状态：pending / approved / rejected';
COMMENT ON COLUMN refund_requests.admin_id IS '审核管理员';
COMMENT ON COLUMN refund_requests.admin_note IS '管理员备注';
COMMENT ON COLUMN refund_requests.created_at IS '申请时间';
COMMENT ON COLUMN refund_requests.updated_at IS '处理时间';

COMMENT ON TABLE payment_orders IS '支付订单表：充值/订阅订单';
COMMENT ON COLUMN payment_orders.id IS '自增主键';
COMMENT ON COLUMN payment_orders.order_id IS '内部订单号';
COMMENT ON COLUMN payment_orders.user_id IS '用户 ID';
COMMENT ON COLUMN payment_orders.order_type IS '类型：recharge（充值）/ subscription（订阅）';
COMMENT ON COLUMN payment_orders.amount IS '金额（分）';
COMMENT ON COLUMN payment_orders.token_amount IS 'Token 数量';
COMMENT ON COLUMN payment_orders.payment_channel IS '渠道：alipay / wechat';
COMMENT ON COLUMN payment_orders.status IS '状态：pending / paid / failed / refunded';
COMMENT ON COLUMN payment_orders.trade_no IS '第三方交易号';
COMMENT ON COLUMN payment_orders.created_at IS '创建时间';
COMMENT ON COLUMN payment_orders.paid_at IS '支付时间';

COMMENT ON TABLE system_configs IS '系统配置表：键值对配置';
COMMENT ON COLUMN system_configs.id IS '自增主键';
COMMENT ON COLUMN system_configs.key IS '配置键名';
COMMENT ON COLUMN system_configs.value IS '配置值';
COMMENT ON COLUMN system_configs.description IS '配置描述';
COMMENT ON COLUMN system_configs.updated_by IS '最后修改人';
COMMENT ON COLUMN system_configs.updated_at IS '更新时间';

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