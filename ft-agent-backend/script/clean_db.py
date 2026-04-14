#!/usr/bin/env python3
"""
清除数据库脏数据，只保留管理员、Agent配置、等级配置
"""
import sys
sys.path.insert(0, '.')

from core.database import SessionLocal, User, Agent, UserTier, TokenAccount, TokenTransaction, Subscription, AdminUser, SystemConfig, ConversationHistory, UserMemory, KnowledgeFile

def clean_db():
    db = SessionLocal()
    try:
        print("开始清除数据库...")

        # 保留的表
        keep_tables = {
            'admin_users': AdminUser,
            'agents': Agent,
            'user_tiers': UserTier,
        }

        # 要清除的表
        clear_tables = {
            'users': User,
            'token_accounts': TokenAccount,
            'token_transactions': TokenTransaction,
            'subscriptions': Subscription,
            'conversation_history': ConversationHistory,
            'user_memory': UserMemory,
            'knowledge_files': KnowledgeFile,
        }

        for table_name, model in clear_tables.items():
            count = db.query(model).count()
            if count > 0:
                db.query(model).delete()
                print(f"  [OK] 已清空 {table_name} ({count} 条)")

        db.commit()
        print("\n数据库清理完成！")

        # 打印保留的数据统计
        print("\n=== 保留的数据 ===")
        for table_name, model in keep_tables.items():
            print(f"  {table_name}: {db.query(model).count()} 条")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    clean_db()
