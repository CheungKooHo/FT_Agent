# -*- coding: utf-8 -*-
"""
支付宝支付服务
"""

import os
import time
import random
from typing import Optional, Dict, Any

from core.config import (
    ALIPAY_APP_ID,
    ALIPAY_PRIVATE_KEY,
    ALIPAY_PUBLIC_KEY,
    ALIPAY_SANDBOX,
    PAYMENT_CALLBACK_URL,
    PaymentStatus
)

# 旧版 API 类名
AliPay = None
try:
    from alipay.aop import AliPay as OldAliPay
    AliPay = OldAliPay
except ImportError:
    try:
        from alipay import AliPay as OldAliPay
        AliPay = OldAliPay
    except ImportError:
        pass

HAS_ALIPAY_SDK = AliPay is not None


ALIPAY_GATEWAY_URL = os.getenv("ALIPAY_GATEWAY_URL", "")

class AlipayService:
    """支付宝支付服务"""

    _alipay = None

    @classmethod
    def get_alipay(cls):
        """获取 AliPay 实例"""
        if not HAS_ALIPAY_SDK:
            return None

        if cls._alipay is None:
            if not all([ALIPAY_APP_ID, ALIPAY_PRIVATE_KEY, ALIPAY_PUBLIC_KEY]):
                return None

            # Use custom gateway URL if provided, otherwise use sandbox/prod default
            if ALIPAY_GATEWAY_URL:
                gateway = ALIPAY_GATEWAY_URL
            elif ALIPAY_SANDBOX:
                gateway = "https://openapi.alipaydev.com/gateway.do"
            else:
                gateway = "https://openapi.alipay.com/gateway.do"

            cls._alipay = AliPay(
                appid=ALIPAY_APP_ID,
                app_notify_url=PAYMENT_CALLBACK_URL,
                app_private_key_string=ALIPAY_PRIVATE_KEY,
                alipay_public_key_string=ALIPAY_PUBLIC_KEY,
                sign_type="RSA2",
                verbose=(ALIPAY_SANDBOX and not ALIPAY_GATEWAY_URL)
            )
            # Override gateway if custom URL
            if ALIPAY_GATEWAY_URL:
                cls._alipay._gateway = ALIPAY_GATEWAY_URL
        return cls._alipay

    @staticmethod
    def create_trade(order_id: str, amount: int, subject: str = "Token充值") -> Dict[str, Any]:
        """创建当面付扫码订单"""
        alipay = AlipayService.get_alipay()

        if not alipay:
            return AlipayService._create_mock_trade(order_id, amount, subject)

        total_amount = amount / 100.0

        try:
            result = alipay.api_alipay_trade_precreate(
                out_trade_no=order_id,
                total_amount=total_amount,
                subject=subject,
                timeout_express="30m"
            )

            qr_code = result.get("qr_code")
            if qr_code:
                return {"order_id": order_id, "qr_code": qr_code, "code_url": None}

            return {"order_id": order_id, "error": str(result)}
        except Exception as e:
            error_str = str(e)
            # AliPayValidationError in sandbox - still might have qr_code
            if "AliPayValidationError" in error_str and alipay:
                # Try to extract qr_code from raw response if available
                return {"order_id": order_id, "error": error_str, "mock": True}
            return {"order_id": order_id, "error": error_str, "mock": True}

    @staticmethod
    def _create_mock_trade(order_id: str, amount: int, subject: str) -> Dict[str, Any]:
        return {
            "order_id": order_id,
            "qr_code": f"https://qr.alipay.com/mock_{order_id}",
            "code_url": None,
            "mock": True
        }

    @staticmethod
    def query_trade(order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        alipay = AlipayService.get_alipay()

        if not alipay:
            return {"status": PaymentStatus.PENDING}

        try:
            result = alipay.api_alipay_trade_query(out_trade_no=order_id)
            trade_status = result.get("trade_status")

            status_mapping = {
                "WAIT_BUYER_PAY": PaymentStatus.PENDING,
                "TRADE_CLOSED": PaymentStatus.FAILED,
                "TRADE_SUCCESS": PaymentStatus.PAID,
                "TRADE_FINISHED": PaymentStatus.PAID
            }

            return {
                "status": status_mapping.get(trade_status, PaymentStatus.PENDING),
                "trade_no": result.get("trade_no")
            }
        except Exception:
            return {"status": PaymentStatus.PENDING}

    @staticmethod
    def verify_notification(data: Dict) -> bool:
        """验证回调签名"""
        alipay = AlipayService.get_alipay()
        if not alipay:
            return True

        try:
            signature = data.get("sign")
            sign_data = {k: v for k, v in data.items() if k not in ("sign", "sign_type")}
            return alipay.verify(sign_data, signature)
        except Exception:
            return False

    @staticmethod
    def handle_notify(data: Dict) -> Dict[str, Any]:
        """处理异步通知"""
        if not AlipayService.verify_notification(data):
            return {"success": False, "message": "签名验证失败"}

        trade_status = data.get("trade_status")
        order_id = data.get("out_trade_no")
        trade_no = data.get("trade_no")

        status_mapping = {
            "TRADE_SUCCESS": PaymentStatus.PAID,
            "TRADE_FINISHED": PaymentStatus.PAID,
            "TRADE_CLOSED": PaymentStatus.FAILED
        }

        return {
            "success": True,
            "order_id": order_id,
            "trade_no": trade_no,
            "status": status_mapping.get(trade_status)
        }

    @staticmethod
    def close_trade(order_id: str) -> Dict[str, Any]:
        """关闭订单"""
        alipay = AlipayService.get_alipay()
        if not alipay:
            return {"success": True, "mock": True}

        try:
            alipay.api_alipay_trade_close(out_trade_no=order_id)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}