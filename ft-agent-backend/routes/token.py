# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from core.database import SessionLocal, User, TokenAccount, TokenTransaction
from core.tier_config import TOKEN_PRICE_PER_MILLION
from routes.dependencies import get_current_user

router = APIRouter(prefix="/token", tags=["Token"])


@router.get("/balance")
async def get_token_balance_endpoint(user_id: str, user: User = Depends(get_current_user)):
    """获取用户 Token 余额"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")

    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
        if not account:
            return {
                "status": "success",
                "data": {
                    "balance": 0,
                    "total_purchased": 0,
                    "total_consumed": 0,
                    "total_granted": 0
                }
            }
        return {
            "status": "success",
            "data": {
                "balance": account.balance,
                "total_purchased": account.total_purchased,
                "total_consumed": account.total_consumed,
                "total_granted": account.total_granted
            }
        }
    finally:
        db.close()


@router.get("/transactions")
async def get_token_transactions(user_id: str, limit: int = 50, user: User = Depends(get_current_user)):
    """获取 Token 交易记录"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")

    db = SessionLocal()
    try:
        transactions = db.query(TokenTransaction).filter(
            TokenTransaction.user_id == user_id
        ).order_by(TokenTransaction.created_at.desc()).limit(limit).all()

        return {
            "status": "success",
            "data": [{
                "type": t.transaction_type,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            } for t in transactions]
        }
    finally:
        db.close()


@router.post("/recharge")
async def recharge_token(user_id: str, amount: int, user: User = Depends(get_current_user)):
    """Token 充值（模拟）"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限操作")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="充值数量必须大于0")

    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
        if not account:
            account = TokenAccount(user_id=user_id, balance=0)
            db.add(account)
            db.flush()

        account.balance += amount
        account.total_purchased += amount

        transaction = TokenTransaction(
            user_id=user_id,
            transaction_type="purchase",
            amount=amount,
            balance_after=account.balance,
            description=f"充值 {amount} Token"
        )
        db.add(transaction)
        db.commit()

        return {
            "status": "success",
            "message": "充值成功",
            "data": {"balance": account.balance}
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/price")
async def get_token_price():
    """获取Token价格"""
    return {
        "status": "success",
        "data": {
            "price_per_million": TOKEN_PRICE_PER_MILLION,
            "price_yuan": TOKEN_PRICE_PER_MILLION / 100
        }
    }
