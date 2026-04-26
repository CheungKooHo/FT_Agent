# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from core.database import SessionLocal, AdminUser, Agent
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/agents")
async def admin_list_agents(admin: AdminUser = Depends(get_current_admin_user)):
    """获取 Agent 配置列表"""
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        return {
            "status": "success",
            "data": [{
                "id": a.id,
                "agent_type": a.agent_type,
                "name": a.name,
                "model": a.model,
                "prompt": a.prompt,
                "is_active": a.is_active
            } for a in agents]
        }
    finally:
        db.close()


@router.post("/agents")
async def admin_create_agent(
    agent_type: str,
    name: str,
    prompt: str,
    model: str = "deepseek-chat",
    is_active: bool = True,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """创建 Agent 配置"""
    db = SessionLocal()
    try:
        existing = db.query(Agent).filter(Agent.agent_type == agent_type).first()
        if existing:
            raise HTTPException(status_code=400, detail="Agent 类型已存在")

        agent = Agent(agent_type=agent_type, name=name, prompt=prompt, model=model, is_active=is_active)
        db.add(agent)
        db.commit()

        return {
            "status": "success",
            "message": f"Agent {name} 创建成功",
            "data": {
                "id": agent.id,
                "agent_type": agent.agent_type,
                "name": agent.name,
                "model": agent.model,
                "is_active": agent.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/agents/{agent_id}")
async def admin_update_agent(
    agent_id: int,
    name: Optional[str] = None,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """更新 Agent 配置"""
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")

        if name is not None:
            agent.name = name
        if prompt is not None:
            agent.prompt = prompt
        if model is not None:
            agent.model = model
        if is_active is not None:
            agent.is_active = is_active

        db.commit()

        return {
            "status": "success",
            "message": "Agent 更新成功",
            "data": {
                "id": agent.id,
                "agent_type": agent.agent_type,
                "name": agent.name,
                "model": agent.model,
                "is_active": agent.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/agents/{agent_id}")
async def admin_delete_agent(
    agent_id: int,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """删除 Agent 配置"""
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")

        db.delete(agent)
        db.commit()

        return {"status": "success", "message": "Agent 删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
