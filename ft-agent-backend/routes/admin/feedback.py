# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc

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


@router.get("/feedback/list")
async def admin_get_feedback_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    rating: str = None,
    start_date: str = None,
    end_date: str = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取评价记录列表（分页）"""
    db = SessionLocal()
    try:
        query = db.query(MessageFeedback)

        if rating:
            query = query.filter(MessageFeedback.rating == rating)
        if start_date:
            query = query.filter(MessageFeedback.created_at >= start_date)
        if end_date:
            query = query.filter(MessageFeedback.created_at <= end_date + " 23:59:59")

        total = query.count()
        feedbacks = query.order_by(desc(MessageFeedback.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        # 统计
        stats = {}
        stats["total"] = db.query(func.count(MessageFeedback.id)).scalar()
        stats["likes"] = db.query(func.count(MessageFeedback.id)).filter(MessageFeedback.rating == "like").scalar()
        stats["dislikes"] = db.query(func.count(MessageFeedback.id)).filter(MessageFeedback.rating == "dislike").scalar()
        stats["likeRate"] = round(stats["likes"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0

        return {
            "status": "success",
            "data": {
                "list": [{
                    "id": f.id,
                    "user_id": f.user_id,
                    "session_id": f.session_id,
                    "message_index": f.message_index,
                    "rating": f.rating,
                    "reason": f.reason or "",
                    "created_at": f.created_at.isoformat() if f.created_at else None
                } for f in feedbacks],
                "total": total,
                "stats": stats
            }
        }
    finally:
        db.close()


@router.get("/feedback/reasons")
async def admin_get_dislike_reasons(
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取差评原因列表"""
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
