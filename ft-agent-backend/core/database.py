from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib
import secrets
import os

# 数据库配置
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite 或 postgresql

if DB_TYPE == "postgresql":
    # PostgreSQL 配置
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "agent_db")

    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=10, max_overflow=20)
    print(f"[OK] 使用 PostgreSQL 数据库: {DB_HOST}:{DB_PORT}/{DB_NAME}")
else:
    # SQLite 配置（开发环境）
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    print("[OK] 使用 SQLite 数据库（开发模式）")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 定义用户表
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)      # 用户唯一标识
    username = Column(String, unique=True, index=True)     # 用户名
    password_hash = Column(String)                         # 密码哈希
    email = Column(String, unique=True, index=True, nullable=True)  # 邮箱（可选）
    phone = Column(String, unique=True, index=True, nullable=True)  # 手机号
    nickname = Column(String, nullable=True)               # 昵称
    is_active = Column(Boolean, default=True)              # 是否激活
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def set_password(self, password: str):
        """设置密码（使用 SHA256 哈希）"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def generate_user_id() -> str:
        """生成唯一的用户ID"""
        return f"user_{secrets.token_hex(8)}"

# 定义 Agent 配置表
class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String, unique=True, index=True) # 如 "tax_standard", "tax_pro"（版本即类型）
    name = Column(String)                                # 如 "财税专家-标准版", "财税专家-Pro版"
    model = Column(String, default="deepseek-chat")      # 调用的模型
    prompt = Column(Text)                                # 系统提示词
    is_active = Column(Boolean, default=True)            # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



# 定义对话历史表
class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)                 # 用户ID
    session_id = Column(String, index=True)              # 会话ID（可选，用于区分不同对话会话）
    agent_type = Column(String, index=True)              # 使用的 agent 类型
    role = Column(String)                                # "user" 或 "assistant"
    content = Column(Text)                               # 消息内容
    references = Column(Text, nullable=True)              # 引用知识库文档列表（JSON格式）
    created_at = Column(DateTime, default=datetime.utcnow) # 创建时间

    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_id'),
    )

# 定义用户长期记忆表
class UserMemory(Base):
    __tablename__ = "user_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)                 # 用户ID
    memory_type = Column(String, index=True)             # 记忆类型：preference/fact/habit 等
    key = Column(String)                                 # 记忆的键（如 "favorite_color", "occupation"）
    value = Column(Text)                                 # 记忆的值
    description = Column(Text, nullable=True)            # 描述信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_memory_type', 'user_id', 'memory_type'),
    )


# ===== 新增表 =====

# 用户等级配置表
class UserTier(Base):
    __tablename__ = "user_tiers"

    id = Column(Integer, primary_key=True, index=True)
    tier_code = Column(String, unique=True, index=True)  # "basic", "pro"
    tier_name = Column(String)  # "基础版", "专业版"
    description = Column(Text)
    features = Column(Text)  # JSON 格式的功能列表
    monthly_token_quota = Column(Integer, default=1000)  # 每月免费 Token
    token_per_message = Column(Integer, default=50)  # 每条消息消耗
    price_monthly = Column(Integer, default=0)  # 月费价格（分）
    agent_type = Column(String)  # 关联的 Agent 类型，如 "tax_basic", "tax_pro"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Token 账户表
class TokenAccount(Base):
    __tablename__ = "token_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    balance = Column(Integer, default=0)  # 剩余 Token
    total_purchased = Column(Integer, default=0)  # 累计购买
    total_consumed = Column(Integer, default=0)  # 累计消耗
    total_granted = Column(Integer, default=0)  # 累计赠送
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Token 交易记录表
class TokenTransaction(Base):
    __tablename__ = "token_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    transaction_type = Column(String)  # "grant", "purchase", "consume", "refund"
    amount = Column(Integer)  # 正数=增加, 负数=消耗
    balance_after = Column(Integer)  # 交易后余额
    description = Column(String)
    related_order_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_token_user_type', 'user_id', 'transaction_type'),
    )


# 订阅表
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    tier_id = Column(Integer, index=True)
    status = Column(String)  # "active", "expired", "cancelled"
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    auto_renew = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_sub_user_status', 'user_id', 'status'),
    )


# 管理员表
class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)  # "super_admin", "content_admin", "user_admin"
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


# 系统配置表
class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    description = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 用户-等级关联表
class UserTierRelation(Base):
    __tablename__ = "user_tier_relations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    tier_id = Column(Integer)
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(String, nullable=True)  # "system" 或 admin username

    __table_args__ = (
        Index('idx_utr_user', 'user_id'),
    )


# 知识库文件表
class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    filename = Column(String)
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    file_type = Column(String, default="pdf")
    agent_type = Column(String, nullable=True)  # 上传时关联的 Agent 类型
    doc_id = Column(String, nullable=True)  # 向量库文档ID
    chunk_count = Column(Integer, default=0)  # 切片数量
    is_indexed = Column(Boolean, default=False)   # 是否已索引到 RAG
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_kf_user', 'user_id'),
    )


# 支付订单表
class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(64), unique=True, index=True)  # 内部订单号
    user_id = Column(String, index=True)
    order_type = Column(String)  # "recharge" / "subscription"
    amount = Column(Integer)  # 金额（分）
    token_amount = Column(Integer)  # Token 数量
    payment_channel = Column(String)  # "alipay" / "wechat"
    status = Column(String, default="pending")  # "pending" / "paid" / "failed" / "refunded"
    trade_no = Column(String, nullable=True)  # 第三方交易号
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_po_user', 'user_id'),
        Index('idx_po_status', 'status'),
    )


# 初始化数据库
def init_db():
    Base.metadata.create_all(bind=engine)

    # 迁移：为 conversation_history 表添加 references 列（如果不存在）
    if "sqlite" in str(engine.url):
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                conn.execute(text('ALTER TABLE conversation_history ADD COLUMN "references" TEXT'))
                conn.commit()
                print("[OK] conversation_history.references 列已添加")
            except Exception:
                pass  # 列已存在

    print(f"[OK] 数据库表初始化完成")