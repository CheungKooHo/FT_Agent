-- FT-Agent PostgreSQL 数据库表结构
-- 生产环境使用

-- 用户表
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(255) UNIQUE,
  nickname VARCHAR(255),
  avatar_url VARCHAR(255),
  bio TEXT,
  email_verified BOOLEAN DEFAULT FALSE,
  email_verification_code VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP
);

CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- 管理员表
CREATE TABLE admin_users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(255) DEFAULT 'user_admin',
  is_active BOOLEAN DEFAULT TRUE,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent 配置表
CREATE TABLE agents (
  id SERIAL PRIMARY KEY,
  agent_type VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  model VARCHAR(255) DEFAULT 'deepseek-chat',
  prompt TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话历史表
CREATE TABLE conversation_history (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255),
  agent_type VARCHAR(255),
  role VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  references TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_session ON conversation_history(user_id, session_id);
CREATE INDEX idx_conversation_user ON conversation_history(user_id);

-- 用户长期记忆表
CREATE TABLE user_memory (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  memory_type VARCHAR(255) NOT NULL,
  key VARCHAR(255) NOT NULL,
  value TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_memory_type ON user_memory(user_id, memory_type);

-- 用户等级配置表
CREATE TABLE user_tiers (
  id SERIAL PRIMARY KEY,
  tier_code VARCHAR(255) UNIQUE NOT NULL,
  tier_name VARCHAR(255) NOT NULL,
  description TEXT,
  features TEXT,
  monthly_token_quota INTEGER DEFAULT 1000,
  token_per_message INTEGER DEFAULT 50,
  price_monthly INTEGER DEFAULT 0,
  agent_type VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token 账户表
CREATE TABLE token_accounts (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) UNIQUE NOT NULL,
  balance INTEGER DEFAULT 0,
  total_purchased INTEGER DEFAULT 0,
  total_consumed INTEGER DEFAULT 0,
  total_granted INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_token_user ON token_accounts(user_id);

-- Token 交易记录表
CREATE TABLE token_transactions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  transaction_type VARCHAR(255) NOT NULL,
  amount INTEGER NOT NULL,
  balance_after INTEGER NOT NULL,
  description VARCHAR(255),
  related_order_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_token_user_type ON token_transactions(user_id, transaction_type);

-- 订阅表
CREATE TABLE subscriptions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  tier_id INTEGER NOT NULL,
  status VARCHAR(255) NOT NULL,
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP NOT NULL,
  auto_renew BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sub_user_status ON subscriptions(user_id, status);

-- 用户-等级关联表
CREATE TABLE user_tier_relations (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  tier_id INTEGER NOT NULL,
  granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  granted_by VARCHAR(255)
);

CREATE INDEX idx_utr_user ON user_tier_relations(user_id);

-- 知识库文件表
CREATE TABLE knowledge_files (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  filename VARCHAR(255) NOT NULL,
  original_filename VARCHAR(255),
  file_path VARCHAR(255),
  file_size INTEGER DEFAULT 0,
  file_type VARCHAR(255) DEFAULT 'pdf',
  agent_type VARCHAR(255),
  doc_id VARCHAR(255),
  chunk_count INTEGER DEFAULT 0,
  is_indexed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kf_user ON knowledge_files(user_id);

-- 通知表
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  notification_type VARCHAR(255) NOT NULL,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notif_user ON notifications(user_id);
CREATE INDEX idx_notif_read ON notifications(is_read);

-- 审计日志表
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255),
  username VARCHAR(255),
  action VARCHAR(255) NOT NULL,
  target_type VARCHAR(255),
  target_id VARCHAR(255),
  details TEXT,
  ip_address VARCHAR(255),
  user_agent VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_target ON audit_logs(target_type, target_id);
CREATE INDEX idx_audit_time ON audit_logs(created_at);

-- 对话满意度评价表
CREATE TABLE message_feedback (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255) NOT NULL,
  message_index INTEGER NOT NULL,
  rating VARCHAR(255) NOT NULL,
  reason VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_session ON message_feedback(session_id);

-- 退款申请表
CREATE TABLE refund_requests (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  reason TEXT,
  status VARCHAR(255) DEFAULT 'pending',
  admin_id VARCHAR(255),
  admin_note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refund_order ON refund_requests(order_id);
CREATE INDEX idx_refund_user ON refund_requests(user_id);
CREATE INDEX idx_refund_status ON refund_requests(status);

-- 支付订单表
CREATE TABLE payment_orders (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) UNIQUE NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  order_type VARCHAR(255) NOT NULL,
  amount INTEGER NOT NULL,
  token_amount INTEGER NOT NULL,
  payment_channel VARCHAR(255) NOT NULL,
  status VARCHAR(255) DEFAULT 'pending',
  trade_no VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  paid_at TIMESTAMP
);

CREATE INDEX idx_po_user ON payment_orders(user_id);
CREATE INDEX idx_po_status ON payment_orders(status);

-- 系统配置表
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

-- 插入默认 Agent 配置
INSERT INTO agents (agent_type, name, model, prompt, is_active) VALUES
('tax_basic', '财税专家-基础版', 'deepseek-chat',
 '你是一个专业的财税助手，帮助用户解答税务和财务相关问题。基础版提供基础的税务咨询服务。', TRUE),
('tax_pro', '财税专家-专业版', 'deepseek-chat',
 '你是一个专业的财税助手，帮助用户解答税务和财务相关问题。专业版提供更深入、更全面的税务筹划和咨询服务。', TRUE)
ON CONFLICT (agent_type) DO NOTHING;

-- 插入默认订阅等级
INSERT INTO user_tiers (tier_code, tier_name, description, features, monthly_token_quota, token_per_message, price_monthly, agent_type) VALUES
('basic', '基础版', '适合个人用户的基础订阅', '["基础税务咨询", "知识库检索", "历史记录"]', 1000, 50, 0, 'tax_basic'),
('pro', '专业版', '适合企业用户的专业订阅', '["基础税务咨询", "知识库检索", "历史记录", "高级税务筹划", "优先响应"]', 5000, 30, 9900, 'tax_pro')
ON CONFLICT (tier_code) DO NOTHING;

-- 插入默认管理员账号 (密码: admin123)
INSERT INTO admin_users (username, password_hash, role) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'super_admin')
ON CONFLICT (username) DO NOTHING;
