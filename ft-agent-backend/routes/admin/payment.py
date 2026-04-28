# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.database import SessionLocal, PaymentOrder, User
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/payment", tags=["Admin支付管理"])


@router.get("/orders")
async def admin_get_payment_orders(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    admin: User = Depends(get_current_admin_user)
):
    """获取支付订单列表（管理后台）"""
    db = SessionLocal()
    try:
        query = db.query(PaymentOrder)

        if status:
            query = query.filter(PaymentOrder.status == status)
        if channel:
            query = query.filter(PaymentOrder.payment_channel == channel)

        total = query.count()

        orders = query.order_by(
            PaymentOrder.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "status": "success",
            "data": {
                "orders": [{
                    "order_id": o.order_id,
                    "user_id": o.user_id,
                    "order_type": o.order_type,
                    "amount": o.amount,
                    "token_amount": o.token_amount,
                    "payment_channel": o.payment_channel,
                    "status": o.status,
                    "trade_no": o.trade_no,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                    "paid_at": o.paid_at.isoformat() if o.paid_at else None
                } for o in orders],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }
    finally:
        db.close()
