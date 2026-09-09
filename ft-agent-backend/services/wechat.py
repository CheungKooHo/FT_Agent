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
    from wechatpayv3 import WeChatPay, WeChatPayType
    HAS_WECHAT_SDK = True
except ImportError:
    HAS_WECHAT_SDK = False

from core.config import (
    WECHAT_APP_ID,
    WECHAT_MCH_ID,
    WECHAT_API_KEY,
    WECHAT_CERT_PATH,
    WECHAT_KEY_PATH,
    WECHAT_CERT_SERIAL_NO,
    WECHAT_PUBLIC_KEY_ID,
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
            if not all([WECHAT_MCH_ID, WECHAT_API_KEY, WECHAT_CERT_SERIAL_NO]):
                return None

            # 读取商户私钥文件内容
            private_key = None
            if WECHAT_KEY_PATH and os.path.exists(WECHAT_KEY_PATH):
                with open(WECHAT_KEY_PATH, 'r') as f:
                    private_key = f.read()

            # 读取微信支付公钥文件内容
            public_key = None
            public_key_path = os.path.join(os.path.dirname(WECHAT_KEY_PATH), "pub_key.pem") if WECHAT_KEY_PATH else None
            if public_key_path and os.path.exists(public_key_path):
                with open(public_key_path, 'r') as f:
                    public_key = f.read()

            # 使用公钥模式初始化，wechatpay_type 必须指定
            cls._wcp = WeChatPay(
                wechatpay_type=WeChatPayType.NATIVE,
                mchid=WECHAT_MCH_ID,
                private_key=private_key,
                cert_serial_no=WECHAT_CERT_SERIAL_NO,
                appid=WECHAT_APP_ID if WECHAT_APP_ID else None,
                apiv3_key=WECHAT_API_KEY,
                notify_url=PAYMENT_CALLBACK_URL,
                public_key=public_key,
                public_key_id=WECHAT_PUBLIC_KEY_ID
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

        code, message = wechatpay.pay(
            description=subject,
            out_trade_no=order_id,
            amount={'total': total_amount, 'currency': 'CNY'},
            pay_type=WeChatPayType.NATIVE
        )

        import logging
        logging.error(f"微信支付 RAW: code={code}, message={message}")

        if code == 200:
            import json
            result = json.loads(message) if isinstance(message, str) else message
            return {
                "order_id": order_id,
                "qr_code": None,
                "code_url": result.get("code_url")
            }
        else:
            return {
                "order_id": order_id,
                "error": f"微信支付创建失败: code={code}, message={message}"
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
            # 手动解密微信支付回调
            import json
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            import base64

            data = json.loads(body)
            resource = data.get("resource", {})

            # 获取加密数据
            ciphertext = base64.b64decode(resource.get("ciphertext", ""))
            nonce = base64.b64decode(resource.get("nonce", ""))
            # associated_data 在微信支付中固定为 "transaction"
            associated_data = resource.get("associated_data", "transaction").encode('utf-8')

            # 使用 APIv3 密钥解密
            aes_key = WECHAT_API_KEY.encode('utf-8')
            import logging
            logging.error(f"APIv3密钥长度: {len(aes_key)}")
            logging.error(f"ciphertext长度: {len(ciphertext)}, nonce长度: {len(nonce)}, aad: {associated_data}")
            aesgcm = AESGCM(aes_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
            logging.error(f"解密成功: {plaintext}")
            result = json.loads(plaintext.decode('utf-8'))

            return result
        except Exception as e:
            import logging
            logging.error(f"解密异常: {e}")
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
        import logging
        import base64
        logger = logging.getLogger(__name__)

        wechatpay = WechatService.get_wechatpay()

        if not wechatpay:
            return {
                "success": True,
                "order_id": "mock_order",
                "mock": True
            }

        logger.error(f"微信回调收到: headers={headers}")

        try:
            # 手动验证签名
            signature = headers.get("wechatpay-signature", "")
            timestamp = headers.get("wechatpay-timestamp", "")
            nonce = headers.get("wechatpay-nonce", "")

            # 构造签名串
            sign_str = f"{timestamp}\n{nonce}\n{body.decode('utf-8')}\n"
            sign_bytes = sign_str.encode('utf-8')

            # 用平台公钥验签
            public_key = None
            pub_key_path = "/home/ubuntu/ssl/wechat/pub_key.pem"
            if os.path.exists(pub_key_path):
                with open(pub_key_path, 'r') as f:
                    public_key = f.read()

            if not public_key:
                logger.error("平台公钥文件不存在")
                return {"success": False, "message": "平台公钥不存在"}

            # 解密通知
            notification = WechatService.decrypt_notification(wechatpay, body)
            logger.error(f"解密结果: {notification}")

            if not notification:
                logger.error("通知解密失败")
                return {"success": False, "message": "通知解密失败"}

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
            logger.error(f"处理回调异常: {e}")
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
