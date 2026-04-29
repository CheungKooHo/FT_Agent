# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc

from core.database import SessionLocal, Notification, AdminUser
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/notifications", tags=["Admin通知管理"])


@router.get("/list")
async def admin_get_notification_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    notification_type: str = None,
    is_read: str = None,
    start_date: str = None,
    end_date: str = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取通知记录列表（分页）"""
    db = SessionLocal()
    try:
        query = db.query(Notification)

        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        if is_read == "true":
            query = query.filter(Notification.is_read == True)
        elif is_read == "false":
            query = query.filter(Notification.is_read == False)
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        if end_date:
            query = query.filter(Notification.created_at <= end_date + " 23:59:59")

        total = query.count()
        notifications = query.order_by(desc(Notification.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "status": "success",
            "data": {
                "list": [{
                    "id": n.id,
                    "user_id": n.user_id,
                    "notification_type": n.notification_type,
                    "title": n.title,
                    "content": n.content,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat() if n.created_at else None
                } for n in notifications],
                "total": total
            }
        }
    finally:
        db.close()


@router.post("/create")
async def admin_create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    content: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """创建通知"""
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content
        )
        db.add(notification)
        db.commit()
        return {"status": "success", "message": "通知已创建", "data": {"id": notification.id}}
    finally:
        db.close()


@router.post("/broadcast")
async def admin_broadcast_notification(
    notification_type: str,
    title: str,
    content: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """广播通知给所有用户"""
    from core.database import User
    db = SessionLocal()
    try:
        users = db.query(User.user_id).all()
        count = 0
        for (uid,) in users:
            notification = Notification(
                user_id=uid,
                notification_type=notification_type,
                title=title,
                content=content
            )
            db.add(notification)
            count += 1
        db.commit()
        return {"status": "success", "message": f"已向 {count} 个用户发送通知"}
    finally:
        db.close()


@router.delete("/{notification_id}")
async def admin_delete_notification(
    notification_id: int,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """删除通知"""
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return {"status": "error", "message": "通知不存在"}
        db.delete(notification)
        db.commit()
        return {"status": "success", "message": "通知已删除"}
    finally:
        db.close()


@router.get("/stats")
async def admin_get_notification_stats(
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取通知统计数据"""
    db = SessionLocal()
    try:
        total = db.query(func.count(Notification.id)).scalar()
        unread = db.query(func.count(Notification.id)).filter(Notification.is_read == False).scalar()

        type_stats = db.query(
            Notification.notification_type,
            func.count(Notification.id)
        ).group_by(Notification.notification_type).all()

        return {
            "status": "success",
            "data": {
                "total": total,
                "unread": unread,
                "read": total - unread,
                "type_stats": [{"type": t, "count": c} for t, c in type_stats]
            }
        }
    finally:
        db.close()