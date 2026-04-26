# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from core.database import SessionLocal, AdminUser, SystemConfig
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin系统"])


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
