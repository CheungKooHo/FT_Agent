"""
初始化数据库数据
包括: Tier配置、管理员账户、系统配置、默认Agent等
"""
import sys
sys.path.insert(0, '.')

from core.database import SessionLocal, UserTier, AdminUser, SystemConfig, Agent
from core.tier_config import TIER_CONFIGS, FREE_TOKEN_GRANT, TOKEN_PRICE_PER_MILLION


def init_agents():
    """初始化默认 Agent"""
    db = SessionLocal()
    try:
        agents_data = {
            "tax_basic": {
                "name": "财税专家-基础版",
                "model": "deepseek-chat",
                "prompt": TIER_CONFIGS["basic"]["system_prompt"],
                "is_active": True
            },
            "tax_pro": {
                "name": "财税专家-专业版",
                "model": "deepseek-chat",
                "prompt": TIER_CONFIGS["pro"]["system_prompt"],
                "is_active": True
            }
        }
        for agent_type, data in agents_data.items():
            existing = db.query(Agent).filter(Agent.agent_type == agent_type).first()
            if not existing:
                agent = Agent(agent_type=agent_type, **data)
                db.add(agent)
                print(f"  + 创建 Agent: {agent_type}")
            else:
                print(f"  = Agent 已存在: {agent_type}")
        db.commit()
    finally:
        db.close()


def init_tiers():
    """初始化 Tier 配置"""
    db = SessionLocal()
    try:
        for tier_code, config in TIER_CONFIGS.items():
            existing = db.query(UserTier).filter(UserTier.tier_code == tier_code).first()
            if not existing:
                tier = UserTier(
                    tier_code=tier_code,
                    tier_name=config["name"],
                    description=config["description"],
                    features=",".join(config["features"]),
                    monthly_token_quota=config["monthly_token_quota"],
                    token_per_message=config["token_per_message"],
                    price_monthly=config["price_monthly"],
                    agent_type=config["agent_type"],
                    is_active=True
                )
                db.add(tier)
                print(f"  + 创建 Tier: {config['name']} -> {config['agent_type']}")
            else:
                print(f"  = Tier 已存在: {config['name']}")
        db.commit()
    finally:
        db.close()


def init_admin():
    """初始化管理员账户"""
    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if not existing:
            admin = AdminUser(
                username="admin",
                role="super_admin",
                is_active=True
            )
            admin.set_password("admin123")
            db.add(admin)
            db.commit()
            print("  + 创建管理员账户: admin / admin123")
        else:
            print("  = 管理员账户已存在")
    finally:
        db.close()


def init_system_configs():
    """初始化系统配置"""
    db = SessionLocal()
    try:
        configs = {
            "FREE_TOKEN_GRANT": str(FREE_TOKEN_GRANT),
            "TOKEN_PRICE_PER_MILLION": str(TOKEN_PRICE_PER_MILLION),
            "SYSTEM_NAME": "财税 Agent 平台",
            "VERSION": "1.0.0"
        }

        for key, value in configs.items():
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not existing:
                config = SystemConfig(key=key, value=value)
                db.add(config)
                print(f"  + 创建配置: {key}={value}")
            else:
                print(f"  = 配置已存在: {key}")
        db.commit()
    finally:
        db.close()


def main():
    print("=" * 50)
    print("初始化数据库...")
    print("=" * 50)

    print("\n[1/4] 初始化默认 Agent...")
    init_agents()

    print("\n[2/4] 初始化 Tier 配置...")
    init_tiers()

    print("\n[3/4] 初始化管理员账户...")
    init_admin()

    print("\n[4/4] 初始化系统配置...")
    init_system_configs()

    print("\n" + "=" * 50)
    print("初始化完成!")
    print("=" * 50)
    print("\n默认管理员: admin / admin123")
    print("请及时修改管理员密码!")
    print("=" * 50)


if __name__ == "__main__":
    main()
