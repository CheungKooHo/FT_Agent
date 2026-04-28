# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from core.database import SessionLocal, User, Notification
from routes.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["通知"])


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    content: str
    is_read: bool
    created_at: str


@router.get("")
async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    user: User = Depends(get_current_user)
):
    """获取用户通知列表"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")

    db = SessionLocal()
    try:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
        return {
            "status": "success",
            "data": [{
                "id": n.id,
                "notification_type": n.notification_type,
                "title": n.title,
                "content": n.content,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifications]
        }
    finally:
        db.close()


@router.get("/unread-count")
async def get_unread_count(
    user_id: str,
    user: User = Depends(get_current_user)
):
    """获取未读通知数量"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")

    db = SessionLocal()
    try:
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        return {"status": "success", "data": {"count": count}}
    finally:
        db.close()


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    user_id: str,
    user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")

    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if not notification:
            raise HTTPException(status_code=404, detail="通知不存在")
        notification.is_read = True
        db.commit()
        return {"status": "success", "message": "已标记为已读"}
    finally:
        db.close()


@router.post("/read-all")
async def mark_all_as_read(
    user_id: str,
    user: User = Depends(get_current_user)
):
    """标记所有通知为已读"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")

    db = SessionLocal()
    try:
        db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({Notification.is_read: True})
        db.commit()
        return {"status": "success", "message": "已全部标记为已读"}
    finally:
        db.close()


def create_notification(db, user_id: str, notification_type: str, title: str, content: str):
    """创建通知（内部函数）"""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content
    )
    db.add(notification)
    return notification
