# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from core.database import SessionLocal, AuditLog, User
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin审计"])


@router.get("/audit-logs")
async def admin_get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin: User = Depends(get_current_admin_user)
):
    """获取审计日志列表"""
    db = SessionLocal()
    try:
        query = db.query(AuditLog)

        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.created_at >= start)
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.created_at <= end)

        total = query.count()

        logs = query.order_by(
            AuditLog.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "status": "success",
            "data": {
                "logs": [{
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat()
                } for log in logs],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }
    finally:
        db.close()


@router.get("/audit-logs/actions")
async def admin_get_action_types(admin: User = Depends(get_current_admin_user)):
    """获取所有操作类型"""
    db = SessionLocal()
    try:
        actions = db.query(AuditLog.action).distinct().all()
        return {
            "status": "success",
            "data": [a[0] for a in actions]
        }
    finally:
        db.close()
