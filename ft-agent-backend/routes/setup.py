# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.database import SessionLocal, Agent

router = APIRouter(prefix="", tags=["Agent配置"])


class SetupAgentRequest(BaseModel):
    name: str
    agent_type: str
    prompt: str


@router.post("/setup_agent")
async def setup_agent(request: SetupAgentRequest):
    """创建或配置 Agent"""
    db = SessionLocal()
    try:
        new_agent = Agent(name=request.name, agent_type=request.agent_type, prompt=request.prompt)
        db.add(new_agent)
        db.commit()
        return {"message": f"Agent {request.name} created!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
