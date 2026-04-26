# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from core.database import SessionLocal, User, Subscription, UserTier, TokenAccount, TokenTransaction
from core.tier_config import TIER_CONFIGS
from routes.dependencies import get_current_user

router = APIRouter(prefix="", tags=["订阅"])


@router.get("/subscription")
async def get_subscription(user_id: str, user: User = Depends(get_current_user)):
    """获取当前订阅信息"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")

    db = SessionLocal()
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).first()

        if not subscription:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
            return {
                "status": "success",
                "data": {
                    "tier": "basic",
                    "tier_name": "基础版",
                    "status": "available",
                    "has_token": account.balance > 0 if account else False,
                    "token_balance": account.balance if account else 0
                }
            }

        tier = db.query(UserTier).filter(UserTier.id == subscription.tier_id).first()

        return {
            "status": "success",
            "data": {
                "tier": tier.tier_code if tier else "basic",
                "tier_name": tier.tier_name if tier else "基础版",
                "status": subscription.status,
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat(),
                "auto_renew": subscription.auto_renew
            }
        }
    finally:
        db.close()


@router.post("/subscription/upgrade")
async def upgrade_subscription(user_id: str, tier_code: str, user: User = Depends(get_current_user)):
    """升级订阅（模拟支付）- 升级时赠送新等级1个月配额"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限操作")
    if tier_code not in TIER_CONFIGS:
        raise HTTPException(status_code=400, detail="无效的订阅等级")

    tier_config = TIER_CONFIGS[tier_code]

    db = SessionLocal()
    try:
        tier = db.query(UserTier).filter(UserTier.tier_code == tier_code).first()
        if not tier:
            raise HTTPException(status_code=404, detail="订阅等级不存在")

        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).first()

        current_tier_code = None
        if existing:
            current_tier = db.query(UserTier).filter(UserTier.id == existing.tier_id).first()
            current_tier_code = current_tier.tier_code if current_tier else None

        grant_tokens = 0
        if existing:
            existing.tier_id = tier.id
            existing.updated_at = datetime.utcnow()
            if current_tier_code == "basic" and tier_code == "pro":
                grant_tokens = tier_config["monthly_token_quota"]
        else:
            subscription = Subscription(
                user_id=user_id,
                tier_id=tier.id,
                status="active",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            db.add(subscription)

        token_granted = 0
        if grant_tokens > 0:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
            if not account:
                account = TokenAccount(user_id=user_id, balance=0)
                db.add(account)
            account.balance += grant_tokens
            account.total_granted += grant_tokens
            transaction = TokenTransaction(
                user_id=user_id,
                transaction_type="grant",
                amount=grant_tokens,
                balance_after=account.balance,
                description=f"升级到{tier.tier_name}赠送 {grant_tokens} Token"
            )
            db.add(transaction)
            token_granted = grant_tokens

        db.commit()

        return {
            "status": "success",
            "message": f"已升级到{tier.tier_name}",
            "data": {
                "tier": tier_code,
                "tier_name": tier.tier_name,
                "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "token_granted": token_granted
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/tiers")
async def get_available_tiers():
    """获取可用订阅等级列表"""
    db = SessionLocal()
    try:
        tiers = db.query(UserTier).filter(UserTier.is_active == True).all()
        return {
            "status": "success",
            "data": [{
                "tier_code": t.tier_code,
                "tier_name": t.tier_name,
                "description": t.description,
                "monthly_token_quota": t.monthly_token_quota,
                "token_per_message": t.token_per_message,
                "price_monthly": t.price_monthly,
                "agent_type": t.agent_type
            } for t in tiers]
        }
    finally:
        db.close()
