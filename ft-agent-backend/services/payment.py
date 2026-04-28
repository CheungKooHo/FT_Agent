# -*- coding: utf-8 -*-
"""
支付服务主入口
"""

import time
import random
from typing import Optional, Dict, Any
from datetime import datetime

from core.database import SessionLocal, PaymentOrder
from core.config import PaymentStatus, PaymentChannel, OrderType
from .alipay import AlipayService
from .wechat import WechatService


class PaymentService:
    """支付服务主入口"""

    @staticmethod
    def create_order(
        user_id: str,
        order_type: str,
        amount: int,
        token_amount: int,
        channel: str
    ) -> Dict[str, Any]:
        """
        创建支付订单

        Args:
            user_id: 用户ID
            order_type: 订单类型 "recharge" / "subscription"
            amount: 金额（分）
            token_amount: Token 数量
            channel: 支付渠道 "alipay" / "wechat"

        Returns:
            创建结果包含 order_id 和 qr 码
        """
        # 生成订单号
        order_id = f"PAY{int(time.time())}{random.randint(1000, 9999)}"

        # 保存到数据库
        db = SessionLocal()
        try:
            payment_order = PaymentOrder(
                order_id=order_id,
                user_id=user_id,
                order_type=order_type,
                amount=amount,
                token_amount=token_amount,
                payment_channel=channel,
                status=PaymentStatus.PENDING
            )
            db.add(payment_order)
            db.commit()

            # 根据渠道创建支付
            subject = "Token充值" if order_type == OrderType.RECHARGE else "订阅升级"

            if channel == PaymentChannel.ALIPAY:
                result = AlipayService.create_trade(order_id, amount, subject)
            else:
                result = WechatService.create_trade(order_id, amount, subject)

            return {
                "status": "success",
                "order_id": order_id,
                "qr_code": result.get("qr_code"),
                "code_url": result.get("code_url"),
                "mock": result.get("mock", False)
            }
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def handle_callback(channel: str, data: Any = None, headers: Dict = None) -> Dict[str, Any]:
        """
        处理支付回调

        Args:
            channel: 支付渠道 "alipay" / "wechat"
            data: 回调数据（支付宝用 dict，微信用 body bytes）
            headers: 回调 headers（微信用）

        Returns:
            处理结果
        """
        try:
            if channel == PaymentChannel.ALIPAY:
                result = AlipayService.handle_notify(data)
            else:
                result = WechatService.handle_notify(headers, data)

            if not result.get("success"):
                return result

            order_id = result.get("order_id")
            trade_no = result.get("trade_no")
            status = result.get("status")

            # 更新订单状态
            db = SessionLocal()
            try:
                order = db.query(PaymentOrder).filter(
                    PaymentOrder.order_id == order_id
                ).first()

                if not order:
                    return {"success": False, "message": "订单不存在"}

                if order.status != PaymentStatus.PENDING:
                    # 订单已处理，可能是重复通知
                    return {"success": True, "message": "订单已处理", "duplicate": True}

                order.status = status
                order.trade_no = trade_no

                if status == PaymentStatus.PAID:
                    order.paid_at = datetime.utcnow()

                    # 执行充值/升级逻辑
                    if order.order_type == OrderType.RECHARGE:
                        PaymentService._process_recharge(order)
                    elif order.order_type == OrderType.SUBSCRIPTION:
                        PaymentService._process_subscription(order)

                db.commit()

                # 发送 Webhook 通知
                PaymentService._send_payment_webhook(order, status)

                return {"success": True, "order_id": order_id, "status": status}
            except Exception as e:
                db.rollback()
                return {"success": False, "message": str(e)}
            finally:
                db.close()
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def _process_recharge(order: PaymentOrder) -> None:
        """处理充值逻辑"""
        from core.database import TokenAccount, TokenTransaction

        db = SessionLocal()
        try:
            account = db.query(TokenAccount).filter(
                TokenAccount.user_id == order.user_id
            ).first()

            if not account:
                account = TokenAccount(user_id=order.user_id, balance=0)
                db.add(account)
                db.flush()

            account.balance += order.token_amount
            account.total_purchased += order.token_amount

            transaction = TokenTransaction(
                user_id=order.user_id,
                transaction_type="purchase",
                amount=order.token_amount,
                balance_after=account.balance,
                description=f"扫码支付充值 {order.token_amount} Token",
                related_order_id=order.order_id
            )
            db.add(transaction)
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _process_subscription(order: PaymentOrder) -> None:
        """处理订阅升级逻辑"""
        from core.database import Subscription, UserTier
        from datetime import timedelta

        db = SessionLocal()
        try:
            tier = db.query(UserTier).filter(
                UserTier.tier_code == "pro"
            ).first()

            if not tier:
                return

            # 检查现有订阅
            existing = db.query(Subscription).filter(
                Subscription.user_id == order.user_id,
                Subscription.status == "active"
            ).first()

            if existing:
                existing.tier_id = tier.id
                existing.updated_at = datetime.utcnow()
            else:
                subscription = Subscription(
                    user_id=order.user_id,
                    tier_id=tier.id,
                    status="active",
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=30)
                )
                db.add(subscription)

            db.commit()
        finally:
            db.close()

    @staticmethod
    def query_order(order_id: str) -> Dict[str, Any]:
        """
        查询订单状态

        Args:
            order_id: 内部订单号

        Returns:
            订单状态信息
        """
        db = SessionLocal()
        try:
            order = db.query(PaymentOrder).filter(
                PaymentOrder.order_id == order_id
            ).first()

            if not order:
                return {"status": "error", "message": "订单不存在"}

            return {
                "status": "success",
                "data": {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "order_type": order.order_type,
                    "amount": order.amount,
                    "token_amount": order.token_amount,
                    "payment_channel": order.payment_channel,
                    "order_status": order.status,
                    "trade_no": order.trade_no,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "paid_at": order.paid_at.isoformat() if order.paid_at else None
                }
            }
        finally:
            db.close()

    @staticmethod
    def close_order(order_id: str) -> Dict[str, Any]:
        """
        关闭订单

        Args:
            order_id: 内部订单号

        Returns:
            关闭结果
        """
        db = SessionLocal()
        try:
            order = db.query(PaymentOrder).filter(
                PaymentOrder.order_id == order_id
            ).first()

            if not order:
                return {"success": False, "message": "订单不存在"}

            if order.status != PaymentStatus.PENDING:
                return {"success": False, "message": "订单已无法关闭"}

            # 关闭第三方订单
            if order.payment_channel == PaymentChannel.ALIPAY:
                AlipayService.close_trade(order_id)
            else:
                WechatService.close_trade(order_id)

            # 更新本地订单状态
            order.status = PaymentStatus.FAILED
            db.commit()

            return {"success": True}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def _send_payment_webhook(order: PaymentOrder, status: str) -> None:
        """发送支付 Webhook 通知"""
        import os
        import asyncio

        webhook_url = os.getenv("WEBHOOK_URL", "")
        if not webhook_url or os.getenv("WEBHOOK_ENABLED", "false").lower() != "true":
            return

        try:
            from services.webhook import get_webhook_service
            webhook_service = get_webhook_service()

            if status == PaymentStatus.PAID:
                asyncio.create_task(
                    webhook_service.send_payment_success(
                        webhook_url,
                        order.order_id,
                        order.user_id,
                        order.amount,
                        order.token_amount
                    )
                )
        except Exception as e:
            print(f"Webhook 通知发送失败: {e}")
