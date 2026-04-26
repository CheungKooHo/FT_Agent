# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from core.database import SessionLocal, User, AdminUser, Subscription, UserTier, UserTierRelation, TokenAccount, TokenTransaction, KnowledgeFile, ConversationHistory
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.put("/users/{user_id}/toggle-status")
async def admin_toggle_user_status(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """启用/禁用用户"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.is_active = not user.is_active
        db.commit()

        return {
            "status": "success",
            "message": f"用户已{'启用' if user.is_active else '禁用'}"
        }
    finally:
        db.close()


@router.post("/users/{user_id}/grant-token")
async def admin_grant_token(
    user_id: str,
    amount: int,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """管理员赠送 Token"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于0")

    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
        if not account:
            account = TokenAccount(user_id=user_id, balance=0)
            db.add(account)

        account.balance += amount
        account.total_granted += amount

        transaction = TokenTransaction(
            user_id=user_id,
            transaction_type="grant",
            amount=amount,
            balance_after=account.balance,
            description=f"管理员 {admin.username} 赠送"
        )
        db.add(transaction)
        db.commit()

        return {
            "status": "success",
            "message": f"已赠送 {amount} Token",
            "data": {"balance": account.balance}
        }
    finally:
        db.close()


@router.get("/users")
async def admin_list_users(
    page: int = 1,
    page_size: int = 20,
    tier: Optional[str] = None,
    is_active: Optional[str] = None,
    search: Optional[str] = None,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取用户列表"""
    db = SessionLocal()
    try:
        query = db.query(User)

        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.nickname.contains(search)) |
                (User.phone.contains(search))
            )

        if is_active is not None:
            is_active_bool = is_active.lower() == 'true' if isinstance(is_active, str) else is_active
            query = query.filter(User.is_active == is_active_bool)

        if tier:
            tier_obj = db.query(UserTier).filter(UserTier.tier_code == tier).first()
            if tier_obj:
                tier_user_ids = [sub.user_id for sub in db.query(Subscription).filter(
                    Subscription.tier_id == tier_obj.id,
                    Subscription.status == "active"
                ).all()]
                query = query.filter(User.user_id.in_(tier_user_ids))
            else:
                query = query.filter(User.user_id.in_([]))

        all_users = query.all()
        total = len(all_users)

        user_data_with_sort = []
        for u in all_users:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == u.user_id).first()
            sub = db.query(Subscription).filter(
                Subscription.user_id == u.user_id,
                Subscription.status == "active"
            ).first()
            tier_obj = None
            if sub:
                tier_obj = db.query(UserTier).filter(UserTier.id == sub.tier_id).first()
            user_tier = db.query(UserTierRelation).filter(UserTierRelation.user_id == u.user_id).first()
            uploaded_files = db.query(KnowledgeFile).filter(KnowledgeFile.user_id == u.user_id).count()

            user_data = {
                "user_id": u.user_id,
                "username": u.username,
                "nickname": u.nickname,
                "email": u.email,
                "phone": u.phone,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "last_login_ts": u.last_login.timestamp() if u.last_login else 0,
                "created_at_ts": u.created_at.timestamp() if u.created_at else 0,
                "token_balance": account.balance if account else 0,
                "token_total_consumed": account.total_consumed if account else 0,
                "token_total_purchased": account.total_purchased if account else 0,
                "tier": tier_obj.tier_code if tier_obj else (user_tier.tier_id if user_tier else "basic"),
                "tier_name": tier_obj.tier_name if tier_obj else "基础版",
                "subscription_end": sub.end_date.isoformat() if sub and sub.end_date else None,
                "subscription_end_ts": sub.end_date.timestamp() if sub and sub.end_date else 0,
                "subscription_status": sub.status if sub else None,
                "uploaded_files": uploaded_files,
                "total_conversations": len(set([c.session_id for c in db.query(ConversationHistory).filter(ConversationHistory.user_id == u.user_id).all()])),
                "total_recharge_tokens": db.query(func.coalesce(func.sum(TokenTransaction.amount), 0)).filter(TokenTransaction.user_id == u.user_id, TokenTransaction.transaction_type == "purchase").scalar()
            }
            user_data_with_sort.append(user_data)

        sort_field = sort_field or "created_at"
        sort_order = sort_order or "desc"
        reverse = sort_order.lower() == "desc"

        sort_field_map = {
            "token_balance": lambda x: x["token_balance"],
            "total_recharge_tokens": lambda x: x["total_recharge_tokens"],
            "total_conversations": lambda x: x["total_conversations"],
            "subscription_end": lambda x: x["subscription_end_ts"],
            "created_at": lambda x: x["created_at_ts"],
            "last_login": lambda x: x["last_login_ts"],
        }

        if sort_field in sort_field_map:
            user_data_with_sort.sort(key=sort_field_map[sort_field], reverse=reverse)

        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = user_data_with_sort[start:end]

        for u in paginated_users:
            u.pop("last_login_ts", None)
            u.pop("created_at_ts", None)
            u.pop("subscription_end_ts", None)

        return {
            "status": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "users": paginated_users
            }
        }
    finally:
        db.close()
