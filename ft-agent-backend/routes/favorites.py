# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import desc

from core.database import SessionLocal, User, MessageFavorite
from routes.dependencies import get_current_user

router = APIRouter(prefix="", tags=["收藏"])


class AddFavoriteRequest(BaseModel):
    content: str
    session_id: Optional[str] = None
    source: Optional[str] = None
    message_id: Optional[str] = None


@router.get("/favorites")
async def get_favorites(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_user)
):
    """获取用户收藏列表"""
    db = SessionLocal()
    try:
        query = db.query(MessageFavorite).filter(
            MessageFavorite.user_id == user.user_id
        ).order_by(desc(MessageFavorite.created_at))

        total = query.count()
        favorites = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "status": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "favorites": [{
                    "id": f.id,
                    "content": f.content,
                    "session_id": f.session_id,
                    "source": f.source,
                    "message_id": f.message_id,
                    "created_at": f.created_at.isoformat()
                } for f in favorites]
            }
        }
    finally:
        db.close()


@router.post("/favorites")
async def add_favorite(
    request: AddFavoriteRequest,
    user: User = Depends(get_current_user)
):
    """添加收藏"""
    db = SessionLocal()
    try:
        favorite = MessageFavorite(
            user_id=user.user_id,
            content=request.content,
            session_id=request.session_id,
            source=request.source,
            message_id=request.message_id
        )
        db.add(favorite)
        db.commit()

        return {
            "status": "success",
            "message": "收藏成功",
            "data": {"id": favorite.id}
        }
    finally:
        db.close()


@router.delete("/favorites/{favorite_id}")
async def delete_favorite(
    favorite_id: int,
    user: User = Depends(get_current_user)
):
    """删除收藏"""
    db = SessionLocal()
    try:
        favorite = db.query(MessageFavorite).filter(
            MessageFavorite.id == favorite_id,
            MessageFavorite.user_id == user.user_id
        ).first()

        if not favorite:
            raise HTTPException(status_code=404, detail="收藏不存在")

        db.delete(favorite)
        db.commit()

        return {"status": "success", "message": "已取消收藏"}
    finally:
        db.close()
