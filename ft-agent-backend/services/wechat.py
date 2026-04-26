# -*- coding: utf-8 -*-
"""
微信支付服务
"""

import os
import time
import random
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path

# 尝试导入 wechatpayv3，如果未安装则使用模拟实现
try:
    from wechatpayv3 import WeChatPay
    HAS_WECHAT_SDK = True
except ImportError:
    HAS_WECHAT_SDK = False

from core.config import (
    WECHAT_APP_ID,
    WECHAT_MCH_ID,
    WECHAT_API_KEY,
    WECHAT_SANDBOX,
    PAYMENT_CALLBACK_URL,
    PaymentStatus
)


class WechatService:
    """微信支付服务"""

    _wcp = None

    @classmethod
    def get_wechatpay(cls) -> Optional[Any]:
        """获取 WeChatPay 实例（延迟初始化）"""
        if not HAS_WECHAT_SDK:
            return None

        if cls._wcp is None:
            if not all([WECHAT_APP_ID, WECHAT_MCH_ID, WECHAT_API_KEY]):
                return None

            cls._wcp = WeChatPay(
                wechatpay_app_id=WECHAT_APP_ID,
                wechatpay_mchid=WECHAT_MCH_ID,
                wechatpay_serial_path=WECHAT_API_KEY,  # API 证书序列号或密钥
                wechatpay_api_key=WECHAT_API_KEY,
                wechatpay_callback_url=PAYMENT_CALLBACK_URL
            )
        return cls._wcp

    @staticmethod
    def create_trade(order_id: str, amount: int, subject: str = "Token充值") -> Dict[str, Any]:
        """
        创建 Native 支付订单

        Args:
            order_id: 内部订单号
            amount: 金额（分）
            subject: 商品描述

        Returns:
            包含 qr_code 或 code_url 的字典
        """
        wechatpay = WechatService.get_wechatpay()

        if not wechatpay:
            # 模拟模式：返回模拟二维码
            return WechatService._create_mock_trade(order_id, amount, subject)

        # 实际调用微信支付
        total_amount = amount  # 微信支付使用分

        code, response = wechatpay.pay(
            description=subject,
            out_trade_no=order_id,
            amount={'total': total_amount, 'currency': 'CNY'},
            notify_url=PAYMENT_CALLBACK_URL
        )

        if code == 200:
            result = response.json()
            return {
                "order_id": order_id,
                "qr_code": None,
                "code_url": result.get("code_url")
            }
        else:
            return {
                "order_id": order_id,
                "error": f"微信支付创建失败: {code}"
            }

    @staticmethod
    def _create_mock_trade(order_id: str, amount: int, subject: str) -> Dict[str, Any]:
        """创建模拟支付订单（用于测试）"""
        return {
            "order_id": order_id,
            "qr_code": None,
            "code_url": f"weixin://wxpay/sandbox/{order_id}",
            "mock": True
        }

    @staticmethod
    def query_trade(order_id: str) -> Dict[str, Any]:
        """
        查询订单状态

        Args:
            order_id: 内部订单号

        Returns:
            订单状态信息
        """
        wechatpay = WechatService.get_wechatpay()

        if not wechatpay:
            # 模拟模式：默认返回pending
            return {"status": PaymentStatus.PENDING}

        try:
            code, response = wechatpay.query(out_trade_no=order_id)

            if code == 200:
                result = response.json()
                trade_state = result.get("trade_state")

                status_mapping = {
                    "SUCCESS": PaymentStatus.PAID,
                    "REFUND": PaymentStatus.REFUNDED,
                    "NOTPAY": PaymentStatus.PENDING,
                    "CLOSED": PaymentStatus.FAILED,
                    "PAYERROR": PaymentStatus.FAILED
                }

                return {
                    "status": status_mapping.get(trade_state, PaymentStatus.PENDING),
                    "trade_no": result.get("transaction_id"),
                    "trade_state": trade_state
                }
            else:
                return {"status": PaymentStatus.PENDING, "error": f"查询失败: {code}"}
        except Exception as e:
            return {"status": PaymentStatus.PENDING, "error": str(e)}

    @staticmethod
    def verify_notification(wechatpay: Any, headers: Dict, body: bytes) -> bool:
        """
        验证回调签名

        Args:
            wechatpay: WeChatPay 实例
            headers: 回调 headers
            body: 回调 body

        Returns:
            是否验证通过
        """
        if not wechatpay:
            return True

        try:
            # 使用 SDK 验证签名
            return wechatpay.verify(headers, body)
        except Exception:
            return False

    @staticmethod
    def decrypt_notification(wechatpay: Any, body: bytes) -> Dict[str, Any]:
        """
        解密通知数据

        Args:
            wechatpay: WeChatPay 实例
            body: 通知 body

        Returns:
            解密后的数据
        """
        if not wechatpay:
            return {}

        try:
            result = wechatpay.intercept_notification(headers={}, body=body)
            return result
        except Exception:
            return {}

    @staticmethod
    def handle_notify(headers: Dict, body: bytes) -> Dict[str, Any]:
        """
        处理异步通知

        Args:
            headers: 通知 headers
            body: 通知 body

        Returns:
            处理结果
        """
        wechatpay = WechatService.get_wechatpay()

        if not wechatpay:
            # 模拟模式：直接返回成功
            return {
                "success": True,
                "order_id": "mock_order",
                "mock": True
            }

        if not WechatService.verify_notification(wechatpay, headers, body):
            return {"success": False, "message": "签名验证失败"}

        try:
            notification = WechatService.decrypt_notification(wechatpay, body)

            order_id = notification.get("out_trade_no")
            trade_no = notification.get("transaction_id")
            trade_state = notification.get("trade_state")

            status_mapping = {
                "SUCCESS": PaymentStatus.PAID,
                "REFUND": PaymentStatus.REFUNDED,
                "CLOSED": PaymentStatus.FAILED
            }

            return {
                "success": True,
                "order_id": order_id,
                "trade_no": trade_no,
                "status": status_mapping.get(trade_state, PaymentStatus.PENDING)
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def close_trade(order_id: str) -> Dict[str, Any]:
        """
        关闭订单

        Args:
            order_id: 内部订单号

        Returns:
            关闭结果
        """
        wechatpay = WechatService.get_wechatpay()

        if not wechatpay:
            return {"success": True, "mock": True}

        try:
            code, response = wechatpay.close(out_trade_no=order_id)

            if code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"关闭失败: {code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
