# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from core.database import SessionLocal, AdminUser, SystemConfig
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin系统"])

# 允许编辑的配置项key列表（安全相关key禁止在此处修改）
ALLOWED_CONFIG_KEYS = {
    "site_name", "site_description", "contact_email",
    "maintenance_mode", "allow_register",
    "default_token_quota", "max_file_upload_size",
    "session_timeout_hours", "rate_limit_enabled",
    "wechat_miniapp_enabled", "sms_enabled"
}

# 禁止通过API修改的key（必须通过环境变量或部署配置）
PROTECTED_CONFIG_KEYS = {
    "jwt_secret_key", "jwt_secret",
    "alipay_app_id", "alipay_private_key", "alipay_public_key",
    "wechat_app_id", "wechat_mch_id", "wechat_api_key",
    "database_url", "redis_url", "secret_key", "encryption_key"
}


@router.get("/system-configs")
async def admin_list_configs(admin: AdminUser = Depends(get_current_admin_user)):
    """获取系统配置"""
    db = SessionLocal()
    try:
        configs = db.query(SystemConfig).all()
        return {
            "status": "success",
            "data": {c.key: c.value for c in configs}
        }
    finally:
        db.close()


@router.put("/system-configs/{key}")
async def admin_update_config(
    key: str,
    value: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """更新系统配置"""
    # 检查是否在禁止修改列表中
    if key.lower() in PROTECTED_CONFIG_KEYS:
        raise HTTPException(status_code=403, detail="此配置项禁止通过API修改")

    # 如果不在允许列表中，给出警告但不阻止
    if key.lower() not in ALLOWED_CONFIG_KEYS:
        # 允许编辑其他key，但记录警告
        pass

    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            config.value = value
            config.updated_by = admin.username
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(key=key, value=value, updated_by=admin.username)
            db.add(config)
        db.commit()

        return {"status": "success", "message": "配置已更新"}
    finally:
        db.close()
