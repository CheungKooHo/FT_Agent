# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from core.database import SessionLocal, AdminUser, UserTier
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/tiers")
async def admin_list_tiers(admin: AdminUser = Depends(get_current_admin_user)):
    """获取订阅版本列表"""
    db = SessionLocal()
    try:
        tiers = db.query(UserTier).all()
        return {
            "status": "success",
            "data": [{
                "id": t.id,
                "tier_code": t.tier_code,
                "tier_name": t.tier_name,
                "description": t.description,
                "monthly_token_quota": t.monthly_token_quota,
                "token_per_message": t.token_per_message,
                "price_monthly": t.price_monthly,
                "agent_type": t.agent_type,
                "is_active": t.is_active
            } for t in tiers]
        }
    finally:
        db.close()


@router.post("/tiers")
async def admin_create_tier(
    tier_code: str,
    tier_name: str,
    description: str,
    monthly_token_quota: int,
    token_per_message: int,
    price_monthly: int,
    agent_type: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """创建订阅版本"""
    db = SessionLocal()
    try:
        existing = db.query(UserTier).filter(UserTier.tier_code == tier_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="版本代码已存在")

        tier = UserTier(
            tier_code=tier_code,
            tier_name=tier_name,
            description=description,
            monthly_token_quota=monthly_token_quota,
            token_per_message=token_per_message,
            price_monthly=price_monthly,
            agent_type=agent_type,
            is_active=True
        )
        db.add(tier)
        db.commit()

        return {
            "status": "success",
            "message": f"订阅版本 {tier_name} 创建成功",
            "data": {
                "id": tier.id,
                "tier_code": tier.tier_code,
                "tier_name": tier.tier_name,
                "agent_type": tier.agent_type
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/tiers/{tier_id}")
async def admin_update_tier(
    tier_id: int,
    tier_name: Optional[str] = None,
    description: Optional[str] = None,
    monthly_token_quota: Optional[int] = None,
    token_per_message: Optional[int] = None,
    price_monthly: Optional[int] = None,
    agent_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """更新订阅版本"""
    db = SessionLocal()
    try:
        tier = db.query(UserTier).filter(UserTier.id == tier_id).first()
        if not tier:
            raise HTTPException(status_code=404, detail="订阅版本不存在")

        if tier_name is not None:
            tier.tier_name = tier_name
        if description is not None:
            tier.description = description
        if monthly_token_quota is not None:
            tier.monthly_token_quota = monthly_token_quota
        if token_per_message is not None:
            tier.token_per_message = token_per_message
        if price_monthly is not None:
            tier.price_monthly = price_monthly
        if agent_type is not None:
            tier.agent_type = agent_type
        if is_active is not None:
            tier.is_active = is_active

        db.commit()

        return {
            "status": "success",
            "message": "订阅版本更新成功",
            "data": {
                "id": tier.id,
                "tier_code": tier.tier_code,
                "tier_name": tier.tier_name,
                "agent_type": tier.agent_type,
                "is_active": tier.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/tiers/{tier_id}")
async def admin_delete_tier(
    tier_id: int,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """删除订阅版本"""
    db = SessionLocal()
    try:
        tier = db.query(UserTier).filter(UserTier.id == tier_id).first()
        if not tier:
            raise HTTPException(status_code=404, detail="订阅版本不存在")

        db.delete(tier)
        db.commit()

        return {"status": "success", "message": "订阅版本删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
