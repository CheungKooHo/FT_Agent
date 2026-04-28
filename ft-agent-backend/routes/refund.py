# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from core.database import SessionLocal, User, PaymentOrder, TokenAccount, TokenTransaction
from routes.dependencies import get_current_user

router = APIRouter(prefix="/refund", tags=["退款"])


class RefundRequest(BaseModel):
    order_id: str
    reason: Optional[str] = ""


@router.post("/request")
async def create_refund_request(
    request: RefundRequest,
    user: User = Depends(get_current_user)
):
    """用户发起退款申请"""
    db = SessionLocal()
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.order_id == request.order_id,
            PaymentOrder.user_id == user.user_id
        ).first()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.status != "paid":
            raise HTTPException(status_code=400, detail="仅已支付的订单可以退款")

        if order.order_type != "recharge":
            raise HTTPException(status_code=400, detail="仅充值订单可以退款")

        # 检查是否已有待处理退款申请
        from core.database import RefundRequest as RefundRequestModel
        existing = db.query(RefundRequestModel).filter(
            RefundRequestModel.order_id == request.order_id,
            RefundRequestModel.status == "pending"
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该订单已有待处理的退款申请")

        refund_req = RefundRequestModel(
            order_id=request.order_id,
            user_id=user.user_id,
            reason=request.reason,
            status="pending"
        )
        db.add(refund_req)
        db.commit()

        return {
            "status": "success",
            "message": "退款申请已提交，请等待管理员审核"
        }
    finally:
        db.close()


@router.get("/my-requests")
async def get_my_refund_requests(
    user: User = Depends(get_current_user)
):
    """获取我的退款申请列表"""
    db = SessionLocal()
    try:
        from core.database import RefundRequest as RefundRequestModel
        requests = db.query(RefundRequestModel).filter(
            RefundRequestModel.user_id == user.user_id
        ).order_by(RefundRequestModel.created_at.desc()).all()

        return {
            "status": "success",
            "data": [{
                "id": r.id,
                "order_id": r.order_id,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat()
            } for r in requests]
        }
    finally:
        db.close()
