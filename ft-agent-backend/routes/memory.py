# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from core.database import User
from core.memory import MemoryManager
from routes.dependencies import get_current_user

router = APIRouter(prefix="", tags=["记忆"])


class MemorySaveRequest(BaseModel):
    user_id: str
    key: str
    value: str
    memory_type: str = "fact"
    description: Optional[str] = None


@router.post("/memory")
async def save_user_memory(request: MemorySaveRequest, user: User = Depends(get_current_user)):
    """保存用户长期记忆"""
    if request.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=request.user_id)
        memory_manager.save_memory(
            key=request.key,
            value=request.value,
            memory_type=request.memory_type,
            description=request.description
        )
        return {"status": "success", "message": "记忆已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{user_id}")
async def get_user_memories(
    user_id: str,
    memory_type: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """获取用户的所有记忆"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id)
        memories = memory_manager.get_all_memories(memory_type=memory_type)
        return {"status": "success", "data": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory")
async def delete_user_memory(
    user_id: str,
    key: str,
    memory_type: str = "fact",
    user: User = Depends(get_current_user)
):
    """删除特定的用户记忆"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id)
        memory_manager.delete_memory(key=key, memory_type=memory_type)
        return {"status": "success", "message": "记忆已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation_history/{user_id}")
async def get_conversation_history(
    user_id: str,
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(get_current_user)
):
    """获取对话历史"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id, session_id=session_id)
        history = memory_manager.get_conversation_history(
            agent_type=agent_type,
            limit=limit
        )
        return {"status": "success", "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation_history")
async def clear_conversation_history(
    user_id: str,
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """清空对话历史"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id, session_id=session_id)
        memory_manager.clear_conversation_history(agent_type=agent_type)
        return {"status": "success", "message": "对话历史已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
