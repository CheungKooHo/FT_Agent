# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from core.database import SessionLocal, User, AdminUser, PaymentOrder, TokenAccount, TokenTransaction, RefundRequest as RefundRequestModel
from routes.dependencies import get_current_admin_user
from services.audit import create_audit_log

router = APIRouter(prefix="/admin", tags=["Admin退款管理"])


@router.get("/refund-requests")
async def admin_get_refund_requests(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取退款申请列表"""
    db = SessionLocal()
    try:
        query = db.query(RefundRequestModel)

        if status:
            query = query.filter(RefundRequestModel.status == status)

        total = query.count()
        requests = query.order_by(
            RefundRequestModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for r in requests:
            order = db.query(PaymentOrder).filter(PaymentOrder.order_id == r.order_id).first()
            user = db.query(User).filter(User.user_id == r.user_id).first()
            result.append({
                "id": r.id,
                "order_id": r.order_id,
                "user_id": r.user_id,
                "username": user.username if user else None,
                "reason": r.reason,
                "status": r.status,
                "admin_note": r.admin_note,
                "amount": order.amount if order else 0,
                "token_amount": order.token_amount if order else 0,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            })

        return {
            "status": "success",
            "data": {
                "requests": result,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }
    finally:
        db.close()


@router.post("/refund-requests/{request_id}/approve")
async def admin_approve_refund(
    request_id: int,
    admin_note: Optional[str] = "",
    admin: AdminUser = Depends(get_current_admin_user)
):
    """审核通过退款申请"""
    db = SessionLocal()
    try:
        refund_req = db.query(RefundRequestModel).filter(
            RefundRequestModel.id == request_id
        ).first()

        if not refund_req:
            raise HTTPException(status_code=404, detail="退款申请不存在")

        if refund_req.status != "pending":
            raise HTTPException(status_code=400, detail="该申请已处理")

        order = db.query(PaymentOrder).filter(
            PaymentOrder.order_id == refund_req.order_id
        ).first()

        if not order or order.status != "paid":
            raise HTTPException(status_code=400, detail="关联订单状态异常")

        # 更新退款申请状态
        refund_req.status = "approved"
        refund_req.admin_id = admin.user_id
        refund_req.admin_note = admin_note
        refund_req.updated_at = datetime.utcnow()

        # 更新订单状态
        order.status = "refunded"

        # 扣除用户 Token（退款金额对应的 Token）
        account = db.query(TokenAccount).filter(
            TokenAccount.user_id == refund_req.user_id
        ).first()

        if account and account.balance >= order.token_amount:
            account.balance -= order.token_amount

            transaction = TokenTransaction(
                user_id=refund_req.user_id,
                transaction_type="refund",
                amount=-order.token_amount,
                balance_after=account.balance,
                description=f"退款返还: 订单 {order.order_id}",
                related_order_id=order.order_id
            )
            db.add(transaction)
        elif account:
            # 余额不足，只记录负向变动
            transaction = TokenTransaction(
                user_id=refund_req.user_id,
                transaction_type="refund",
                amount=-min(account.balance, order.token_amount),
                balance_after=0,
                description=f"退款返还: 订单 {order.order_id}（部分扣除，余额不足）",
                related_order_id=order.order_id
            )
            db.add(transaction)
            account.balance = 0

        db.commit()

        create_audit_log(
            db,
            user_id=admin.user_id,
            username=admin.username,
            action="approve_refund",
            target_type="refund_request",
            target_id=str(request_id),
            details={
                "order_id": order.order_id,
                "token_amount": order.token_amount,
                "admin_note": admin_note
            }
        )

        return {
            "status": "success",
            "message": "退款已通过，Token 已扣除"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/refund-requests/{request_id}/reject")
async def admin_reject_refund(
    request_id: int,
    admin_note: Optional[str] = "",
    admin: AdminUser = Depends(get_current_admin_user)
):
    """审核拒绝退款申请"""
    db = SessionLocal()
    try:
        refund_req = db.query(RefundRequestModel).filter(
            RefundRequestModel.id == request_id
        ).first()

        if not refund_req:
            raise HTTPException(status_code=404, detail="退款申请不存在")

        if refund_req.status != "pending":
            raise HTTPException(status_code=400, detail="该申请已处理")

        refund_req.status = "rejected"
        refund_req.admin_id = admin.user_id
        refund_req.admin_note = admin_note
        refund_req.updated_at = datetime.utcnow()

        db.commit()

        create_audit_log(
            db,
            user_id=admin.user_id,
            username=admin.username,
            action="reject_refund",
            target_type="refund_request",
            target_id=str(request_id),
            details={"admin_note": admin_note}
        )

        return {
            "status": "success",
            "message": "退款申请已拒绝"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
