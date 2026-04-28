# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional

from core.database import User
from services.payment import PaymentService
from routes.dependencies import get_current_user

router = APIRouter(prefix="/payment", tags=["支付"])


class CreatePaymentOrderRequest(BaseModel):
    order_type: str
    amount: int
    token_amount: int
    channel: str


@router.post("/create")
async def create_payment_order(
    request: CreatePaymentOrderRequest,
    user: User = Depends(get_current_user)
):
    """创建支付订单"""
    try:
        result = PaymentService.create_order(
            user_id=user.user_id,
            order_type=request.order_type,
            amount=request.amount,
            token_amount=request.token_amount,
            channel=request.channel
        )

        if result.get("status") == "success":
            return {
                "status": "success",
                "order_id": result["order_id"],
                "qr_code": result.get("qr_code"),
                "code_url": result.get("code_url")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback/{channel}")
async def payment_callback(channel: str, request: Request):
    """支付回调"""
    try:
        if channel == "alipay":
            form_data = await request.form()
            data = dict(form_data)
            result = PaymentService.handle_callback(channel, data)
        elif channel == "wechat":
            body = await request.body()
            headers = dict(request.headers)
            result = PaymentService.handle_callback(channel, body, headers)
        else:
            return {"status": "error", "message": "不支持的支付渠道"}

        if result.get("success"):
            return {"status": "success", "message": "回调处理成功"}
        else:
            return {"status": "error", "message": result.get("message")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{order_id}")
async def get_payment_status(
    order_id: str,
    user: User = Depends(get_current_user)
):
    """查询订单状态"""
    try:
        result = PaymentService.query_order(order_id)

        if result.get("status") == "success":
            data = result["data"]
            if data["user_id"] != user.user_id:
                raise HTTPException(status_code=403, detail="无权限访问")
            return {
                "status": "success",
                "order_id": data["order_id"],
                "order_type": data["order_type"],
                "amount": data["amount"],
                "token_amount": data["token_amount"],
                "payment_channel": data["payment_channel"],
                "status": data["order_status"],
                "trade_no": data["trade_no"],
                "created_at": data["created_at"],
                "paid_at": data["paid_at"]
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("message"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close/{order_id}")
async def close_payment_order(
    order_id: str,
    user: User = Depends(get_current_user)
):
    """关闭订单"""
    try:
        result = PaymentService.close_order(order_id)

        if result.get("success"):
            return {"status": "success", "message": "订单已关闭"}
        else:
            raise HTTPException(status_code=400, detail=result.get("message"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
