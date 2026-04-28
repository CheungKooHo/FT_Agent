# -*- coding: utf-8 -*-
import httpx
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime


class WebhookService:
    """Webhook 服务，用于向外部系统发送事件通知"""

    def __init__(self):
        self.timeout = 10.0  # 超时时间（秒）

    async def send_webhook(self, url: str, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 webhook 请求

        Args:
            url: webhook URL
            event_type: 事件类型
            data: 事件数据

        Returns:
            {"success": bool, "message": str}
        """
        payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    return {"success": True, "message": "Webhook 发送成功"}
                else:
                    return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}
        except httpx.TimeoutException:
            return {"success": False, "message": "Webhook 请求超时"}
        except httpx.RequestError as e:
            return {"success": False, "message": f"Webhook 请求失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Webhook 异常: {str(e)}"}

    async def send_payment_success(self, url: str, order_id: str, user_id: str, amount: int, token_amount: int):
        """支付成功事件"""
        return await self.send_webhook(url, "payment.success", {
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "token_amount": token_amount,
            "paid_at": datetime.utcnow().isoformat() + "Z"
        })

    async def send_user_register(self, url: str, user_id: str, username: str, email: Optional[str] = None):
        """用户注册事件"""
        return await self.send_webhook(url, "user.register", {
            "user_id": user_id,
            "username": username,
            "email": email,
            "registered_at": datetime.utcnow().isoformat() + "Z"
        })

    async def send_subscription_activated(self, url: str, user_id: str, tier_code: str, end_date: str):
        """订阅激活事件"""
        return await self.send_webhook(url, "subscription.activated", {
            "user_id": user_id,
            "tier_code": tier_code,
            "end_date": end_date,
            "activated_at": datetime.utcnow().isoformat() + "Z"
        })

    async def send_subscription_expiring(self, url: str, user_id: str, days_left: int, end_date: str):
        """订阅即将到期事件"""
        return await self.send_webhook(url, "subscription.expiring", {
            "user_id": user_id,
            "days_left": days_left,
            "end_date": end_date,
            "sent_at": datetime.utcnow().isoformat() + "Z"
        })


# 全局单例
_webhook_service = None

def get_webhook_service() -> WebhookService:
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
