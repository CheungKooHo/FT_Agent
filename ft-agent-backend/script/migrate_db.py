"""
数据库迁移脚本
将数据从 SQLite 迁移到 PostgreSQL
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 要迁移的所有表模型
TABLE_MODELS = [
    ("users", "User"),
    ("agents", "Agent"),
    ("user_tiers", "UserTier"),
    ("token_accounts", "TokenAccount"),
    ("token_transactions", "TokenTransaction"),
    ("subscriptions", "Subscription"),
    ("policy_documents", "PolicyDocument"),
    ("admin_users", "AdminUser"),
    ("system_configs", "SystemConfig"),
    ("user_tier_relations", "UserTierRelation"),
    ("knowledge_files", "KnowledgeFile"),
    ("conversation_history", "ConversationHistory"),
    ("user_memory", "UserMemory"),
]


def migrate_database():
    """迁移数据库"""

    print("\n" + "=" * 60)
    print("数据库迁移工具 - SQLite → PostgreSQL")
    print("=" * 60)

    # 1. 检查 PostgreSQL 配置
    print("\n[1/5] 检查配置")

    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\n错误: 缺少以下环境变量:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n请在 .env 文件中配置 PostgreSQL 连接信息")
        return False

    print("[OK] PostgreSQL 配置完整")

    # 2. 连接数据库
    print("\n[2/5] 连接数据库")

    sqlite_url = "sqlite:///./sql_app.db"
    pg_user = os.getenv("DB_USER")
    pg_password = os.getenv("DB_PASSWORD")
    pg_host = os.getenv("DB_HOST")
    pg_port = os.getenv("DB_PORT")
    pg_name = os.getenv("DB_NAME")
    postgresql_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_name}"

    try:
        if not os.path.exists("./sql_app.db"):
            print("[OK] SQLite 数据库不存在，将创建新的 PostgreSQL 数据库")
            target_engine = create_engine(postgresql_url)
            from core.database import Base
            Base.metadata.create_all(bind=target_engine)
            print("[OK] PostgreSQL 表结构已创建")
            return True

        source_engine = create_engine(sqlite_url)
        SourceSession = sessionmaker(bind=source_engine)
        source_session = SourceSession()
        print("[OK] 已连接到 SQLite 数据库")

        target_engine = create_engine(postgresql_url)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        print("[OK] 已连接到 PostgreSQL 数据库")
    except Exception as e:
        print(f"\n连接失败: {str(e)}")
        return False

    try:
        # 导入所有模型
        from core.database import (
            Base, User, Agent, ConversationHistory, UserMemory,
            UserTier, TokenAccount, TokenTransaction, Subscription,
            PolicyDocument, AdminUser, SystemConfig, UserTierRelation,
            KnowledgeFile
        )

        # 在目标数据库创建所有表
        Base.metadata.create_all(bind=target_engine)
        print("[OK] PostgreSQL 表结构已创建")

        # 3. 迁移所有表
        print("\n[3/5] 迁移数据")

        model_map = {
            "User": User,
            "Agent": Agent,
            "UserTier": UserTier,
            "TokenAccount": TokenAccount,
            "TokenTransaction": TokenTransaction,
            "Subscription": Subscription,
            "PolicyDocument": PolicyDocument,
            "AdminUser": AdminUser,
            "SystemConfig": SystemConfig,
            "UserTierRelation": UserTierRelation,
            "KnowledgeFile": KnowledgeFile,
            "ConversationHistory": ConversationHistory,
            "UserMemory": UserMemory,
        }

        total_migrated = 0
        for table_name, model_name in TABLE_MODELS:
            model = model_map[model_name]
            records = source_session.query(model).all()
            count = 0
            for record in records:
                # 使用 merge 避免主键冲突
                target_session.merge(record)
                count += 1
            if count > 0:
                target_session.commit()
            print(f"  {table_name}: {count} 条" + (" [OK]" if count > 0 else " (无数据)"))
            total_migrated += count

        # 4. 验证
        print("\n[4/5] 验证数据")
        for table_name, model_name in TABLE_MODELS:
            model = model_map[model_name]
            target_count = target_session.query(model).count()
            print(f"  {table_name}: {target_count} 条")

        # 5. Qdrant 向量库说明
        print("\n[5/5] Qdrant 向量库迁移说明")
        print("-" * 60)
        print("""
Qdrant 向量库数据存储在 local_qdrant/ 目录，需要手动迁移：

1. 开发环境 → 生产环境：
   - 直接复制整个 local_qdrant/ 目录到新服务器
   - 路径：ft-agent-backend/local_qdrant/

2. Docker 部署：
   - docker-compose 中已配置 volume: backend_qdrant:/app/local_qdrant
   - 该 volume 数据会持久化，无需额外迁移

3. 迁移后验证：
   - 启动服务后，访问管理后台 → 知识库统计
   - 确认 vectors_count 与原环境一致
""")

    except Exception as e:
        print(f"\n迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        target_session.rollback()
        return False
    finally:
        source_session.close()
        target_session.close()

    print("\n" + "=" * 60)
    print(f"✅ 数据库迁移完成！共迁移 {total_migrated} 条记录")
    print("=" * 60)
    print("\n后续步骤:")
    print("1. 验证 PostgreSQL 中的数据是否正确")
    print("2. 修改 .env: 设置 DB_TYPE=postgresql")
    print("3. 重启服务: python main.py")
    print("4. 备份原数据: 保留 sql_app.db 和 local_qdrant/ 作为备份")
    print("=" * 60)

    return True


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    confirm = input("\n警告: 此操作将迁移数据到 PostgreSQL\n确保已经:\n1. 创建了 PostgreSQL 数据库\n2. 在 .env 中配置了正确的数据库连接信息\n3. 备份了现有的 SQLite 数据库和 local_qdrant/\n\n是否继续? (yes/no): ").strip().lower()

    if confirm == "yes":
        success = migrate_database()
        sys.exit(0 if success else 1)
    else:
        print("\n已取消迁移")
        sys.exit(0)