"""
数据库迁移脚本
将数据从 SQLite 迁移到 PostgreSQL
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def migrate_database():
    """迁移数据库"""

    print("\n" + "="*60)
    print("数据库迁移工具 - SQLite → PostgreSQL")
    print("="*60)

    # 1. 检查 PostgreSQL 配置
    print("\n📋 步骤 1: 检查配置")

    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\n❌ 错误: 缺少以下环境变量:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n请在 .env 文件中配置 PostgreSQL 连接信息")
        return False

    print("✓ PostgreSQL 配置完整")

    # 2. 连接到数据库
    print("\n📋 步骤 2: 连接数据库")

    # SQLite 源数据库
    sqlite_url = "sqlite:///./sql_app.db"

    # PostgreSQL 目标数据库
    pg_user = os.getenv("DB_USER")
    pg_password = os.getenv("DB_PASSWORD")
    pg_host = os.getenv("DB_HOST")
    pg_port = os.getenv("DB_PORT")
    pg_name = os.getenv("DB_NAME")
    postgresql_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_name}"

    try:
        # 检查 SQLite 数据库是否存在
        if not os.path.exists("./sql_app.db"):
            print("✓ SQLite 数据库不存在，跳过迁移（将创建新的 PostgreSQL 数据库）")
            return True

        source_engine = create_engine(sqlite_url)
        SourceSession = sessionmaker(bind=source_engine)
        source_session = SourceSession()
        print("✓ 已连接到 SQLite 数据库")

        target_engine = create_engine(postgresql_url)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        print("✓ 已连接到 PostgreSQL 数据库")

    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        return False

    # 3. 迁移数据
    print("\n📋 步骤 3: 迁移数据")

    try:
        # 导入模型
        from core.database import User, AgentConfig, ConversationHistory, UserMemory, Base

        # 在目标数据库创建表
        Base.metadata.create_all(bind=target_engine)
        print("✓ PostgreSQL 表结构已创建")

        # 迁移用户表
        users = source_session.query(User).all()
        if users:
            for user in users:
                # 检查是否已存在
                existing = target_session.query(User).filter(User.user_id == user.user_id).first()
                if not existing:
                    target_session.merge(user)
            target_session.commit()
            print(f"✓ 迁移了 {len(users)} 个用户")
        else:
            print("✓ 无用户数据需要迁移")

        # 迁移 Agent 配置
        agents = source_session.query(AgentConfig).all()
        if agents:
            for agent in agents:
                existing = target_session.query(AgentConfig).filter(AgentConfig.agent_type == agent.agent_type).first()
                if not existing:
                    target_session.merge(agent)
            target_session.commit()
            print(f"✓ 迁移了 {len(agents)} 个 Agent 配置")
        else:
            print("✓ 无 Agent 配置需要迁移")

        # 迁移对话历史
        conversations = source_session.query(ConversationHistory).all()
        if conversations:
            for conv in conversations:
                target_session.merge(conv)
            target_session.commit()
            print(f"✓ 迁移了 {len(conversations)} 条对话记录")
        else:
            print("✓ 无对话历史需要迁移")

        # 迁移用户记忆
        memories = source_session.query(UserMemory).all()
        if memories:
            for memory in memories:
                target_session.merge(memory)
            target_session.commit()
            print(f"✓ 迁移了 {len(memories)} 条用户记忆")
        else:
            print("✓ 无用户记忆需要迁移")

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        target_session.rollback()
        return False
    finally:
        source_session.close()
        target_session.close()

    print("\n✅ 数据迁移完成！")
    print("\n" + "="*60)
    print("下一步:")
    print("1. 验证数据: 检查 PostgreSQL 中的数据是否正确")
    print("2. 修改 .env: 设置 DB_TYPE=postgresql")
    print("3. 重启服务: python main.py")
    print("4. 备份原数据: 保留 sql_app.db 作为备份")
    print("="*60)

    return True

if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()

    print("\n⚠️  警告: 此操作将迁移数据到 PostgreSQL")
    print("确保已经:")
    print("1. 创建了 PostgreSQL 数据库")
    print("2. 在 .env 中配置了正确的数据库连接信息")
    print("3. 备份了现有的 SQLite 数据库")

    confirm = input("\n是否继续? (yes/no): ").strip().lower()

    if confirm == "yes":
        success = migrate_database()
        sys.exit(0 if success else 1)
    else:
        print("\n已取消迁移")
        sys.exit(0)
