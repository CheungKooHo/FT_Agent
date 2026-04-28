# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy import func

from core.database import SessionLocal, MessageFeedback, AdminUser
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin评价统计"])


@router.get("/feedback/stats")
async def admin_get_feedback_stats(
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取评价统计数据"""
    db = SessionLocal()
    try:
        total = db.query(func.count(MessageFeedback.id)).scalar()

        likes = db.query(func.count(MessageFeedback.id)).filter(
            MessageFeedback.rating == "like"
        ).scalar()

        dislikes = db.query(func.count(MessageFeedback.id)).filter(
            MessageFeedback.rating == "dislike"
        ).scalar()

        # 差评原因统计
        reason_stats = db.query(
            MessageFeedback.reason,
            func.count(MessageFeedback.id)
        ).filter(
            MessageFeedback.rating == "dislike",
            MessageFeedback.reason != ""
        ).group_by(MessageFeedback.reason).all()

        return {
            "status": "success",
            "data": {
                "total": total,
                "likes": likes,
                "dislikes": dislikes,
                "like_rate": round(likes / total * 100, 1) if total > 0 else 0,
                "dislike_reasons": [{"reason": r, "count": c} for r, c in reason_stats]
            }
        }
    finally:
        db.close()


@router.get("/feedback/reasons")
async def admin_get_dislike_reasons(
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取差评原因列表（用于配置可选原因）"""
    db = SessionLocal()
    try:
        reasons = db.query(MessageFeedback.reason).filter(
            MessageFeedback.rating == "dislike",
            MessageFeedback.reason != ""
        ).distinct().all()

        return {
            "status": "success",
            "data": [r[0] for r in reasons]
        }
    finally:
        db.close()
