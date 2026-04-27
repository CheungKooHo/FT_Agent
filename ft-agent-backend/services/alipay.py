# -*- coding: utf-8 -*-
"""
支付宝支付服务 (新版 SDK)
"""

import os
from typing import Optional, Dict, Any

from core.config import (
    ALIPAY_APP_ID,
    ALIPAY_PRIVATE_KEY,
    ALIPAY_PUBLIC_KEY,
    ALIPAY_SANDBOX,
    PAYMENT_CALLBACK_URL,
    PaymentStatus
)

# 检查是否配置了支付宝环境变量
_ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
_ALIPAY_PRIVATE_KEY = os.getenv("ALIPAY_PRIVATE_KEY", "").replace("\\n", "\n")
_ALIPAY_PUBLIC_KEY = os.getenv("ALIPAY_PUBLIC_KEY", "").replace("\\n", "\n")
ALIPAY_CONFIGURED = all([_ALIPAY_APP_ID, _ALIPAY_PRIVATE_KEY, _ALIPAY_PUBLIC_KEY])

ALIPAY_GATEWAY_URL = os.getenv("ALIPAY_GATEWAY_URL", "")


class AlipayService:
    """支付宝支付服务"""

    _alipay_client = None

    @classmethod
    def get_alipay_client(cls):
        """获取 AlipayClient 实例"""
        if not ALIPAY_CONFIGURED:
            return None

        if cls._alipay_client is None:
            from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
            from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

            alipay_client_config = AlipayClientConfig(sandbox_debug=ALIPAY_SANDBOX)
            alipay_client_config.app_id = _ALIPAY_APP_ID
            alipay_client_config.app_private_key = _ALIPAY_PRIVATE_KEY
            alipay_client_config.alipay_public_key = _ALIPAY_PUBLIC_KEY
            alipay_client_config.sign_type = "RSA2"

            # Use custom gateway URL if provided
            if ALIPAY_GATEWAY_URL:
                alipay_client_config.server_url = ALIPAY_GATEWAY_URL
            elif ALIPAY_SANDBOX:
                alipay_client_config.server_url = "https://openapi.alipaydev.com/gateway.do"
            else:
                alipay_client_config.server_url = "https://openapi.alipay.com/gateway.do"

            cls._alipay_client = DefaultAlipayClient(
                alipay_client_config=alipay_client_config,
                logger=None
            )

        return cls._alipay_client

    @staticmethod
    def create_trade(order_id: str, amount: int, subject: str = "Token充值") -> Dict[str, Any]:
        """创建当面付扫码订单"""
        client = AlipayService.get_alipay_client()

        if not client:
            return AlipayService._create_mock_trade(order_id, amount, subject)

        from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest
        from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel

        total_amount = f"{amount / 100.0:.2f}"

        model = AlipayTradePrecreateModel()
        model.out_trade_no = order_id
        model.total_amount = total_amount
        model.subject = subject
        model.timeout_express = "30m"

        request = AlipayTradePrecreateRequest(biz_model=model)

        try:
            response = client.execute(request)
            if response and response.get("qr_code"):
                return {
                    "order_id": order_id,
                    "qr_code": response.get("qr_code"),
                    "code_url": None
                }
            return {"order_id": order_id, "error": str(response), "mock": True}
        except Exception as e:
            error_str = str(e)
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
        client = AlipayService.get_alipay_client()

        if not client:
            return {"status": PaymentStatus.PENDING}

        from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
        from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel

        model = AlipayTradeQueryModel()
        model.out_trade_no = order_id

        request = AlipayTradeQueryRequest(biz_model=model)

        try:
            response = client.execute(request)
            trade_status = response.get("trade_status")

            status_mapping = {
                "WAIT_BUYER_PAY": PaymentStatus.PENDING,
                "TRADE_CLOSED": PaymentStatus.FAILED,
                "TRADE_SUCCESS": PaymentStatus.PAID,
                "TRADE_FINISHED": PaymentStatus.PAID
            }

            return {
                "status": status_mapping.get(trade_status, PaymentStatus.PENDING),
                "trade_no": response.get("trade_no")
            }
        except Exception:
            return {"status": PaymentStatus.PENDING}

    @staticmethod
    def verify_notification(data: Dict) -> bool:
        """验证回调签名"""
        if not ALIPAY_CONFIGURED:
            return True

        client = AlipayService.get_alipay_client()
        if not client:
            return True

        try:
            signature = data.get("sign")
            sign_data = {k: v for k, v in data.items() if k not in ("sign", "sign_type")}
            # 新版 SDK 验签方式
            from alipay.aop.api.util.SignatureUtils import verify_with_rsa2
            return verify_with_rsa2(
                _ALIPAY_PUBLIC_KEY,
                sign_data,
                signature
            )
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
            "TRADE_CLOSED": PaymentStatus.FAILED,
            "WAIT_BUYER_PAY": PaymentStatus.PENDING
        }

        status = status_mapping.get(trade_status, PaymentStatus.PENDING)

        return {
            "success": True,
            "order_id": order_id,
            "trade_no": trade_no,
            "status": status
        }

    @staticmethod
    def close_trade(order_id: str) -> Dict[str, Any]:
        """关闭订单"""
        client = AlipayService.get_alipay_client()
        if not client:
            return {"success": True, "mock": True}

        from alipay.aop.api.request.AlipayTradeCloseRequest import AlipayTradeCloseRequest
        from alipay.aop.api.domain.AlipayTradeCloseModel import AlipayTradeCloseModel

        model = AlipayTradeCloseModel()
        model.out_trade_no = order_id

        request = AlipayTradeCloseRequest(biz_model=model)

        try:
            client.execute(request)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
