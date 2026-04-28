# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from core.database import SessionLocal, User, MessageFeedback
from routes.dependencies import get_current_user

router = APIRouter(prefix="/feedback", tags=["评价"])


class FeedbackRequest(BaseModel):
    session_id: str
    message_index: int
    rating: str  # "like" / "dislike"
    reason: Optional[str] = ""


@router.post("")
async def create_feedback(
    request: FeedbackRequest,
    user: User = Depends(get_current_user)
):
    """提交消息评价"""
    if request.rating not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="评价类型无效")

    if request.rating == "dislike" and not request.reason:
        raise HTTPException(status_code=400, detail="请提供差评原因")

    db = SessionLocal()
    try:
        feedback = MessageFeedback(
            user_id=user.user_id,
            session_id=request.session_id,
            message_index=request.message_index,
            rating=request.rating,
            reason=request.reason or ""
        )
        db.add(feedback)
        db.commit()

        return {"status": "success", "message": "评价已提交"}
    finally:
        db.close()


@router.get("/session/{session_id}")
async def get_session_feedback(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """获取会话的所有评价"""
    db = SessionLocal()
    try:
        feedbacks = db.query(MessageFeedback).filter(
            MessageFeedback.user_id == user.user_id,
            MessageFeedback.session_id == session_id
        ).all()

        return {
            "status": "success",
            "data": [{
                "id": f.id,
                "message_index": f.message_index,
                "rating": f.rating,
                "reason": f.reason,
                "created_at": f.created_at.isoformat()
            } for f in feedbacks]
        }
    finally:
        db.close()
