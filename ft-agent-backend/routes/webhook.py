# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import os

from core.database import SessionLocal, SystemConfig
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/webhook", tags=["Webhook管理"])


class WebhookConfigRequest(BaseModel):
    webhook_url: str
    events: List[str]  # "payment.success", "user.register", "subscription.activated", "subscription.expiring"


def get_webhook_config() -> dict:
    """从环境变量或数据库获取 webhook 配置"""
    webhook_config = {
        "enabled": os.getenv("WEBHOOK_ENABLED", "false").lower() == "true",
        "url": os.getenv("WEBHOOK_URL", ""),
        "events": []
    }

    # 从数据库读取自定义配置
    db = SessionLocal()
    try:
        configs = db.query(SystemConfig).filter(
            SystemConfig.key.like("webhook_%")
        ).all()
        for config in configs:
            if config.key == "webhook_enabled":
                webhook_config["enabled"] = config.value == "true"
            elif config.key == "webhook_url":
                webhook_config["url"] = config.value
            elif config.key == "webhook_events":
                webhook_config["events"] = config.value.split(",") if config.value else []
    finally:
        db.close()

    return webhook_config


@router.post("/config")
async def configure_webhook(request: WebhookConfigRequest, admin=Depends(get_current_admin_user)):
    """配置 Webhook URL 和事件类型"""
    db = SessionLocal()
    try:
        # 保存 Webhook URL
        url_config = db.query(SystemConfig).filter(SystemConfig.key == "webhook_url").first()
        if url_config:
            url_config.value = request.webhook_url
        else:
            url_config = SystemConfig(
                key="webhook_url",
                value=request.webhook_url,
                description="Webhook 通知地址"
            )
            db.add(url_config)

        # 保存启用状态
        enabled_config = db.query(SystemConfig).filter(SystemConfig.key == "webhook_enabled").first()
        if enabled_config:
            enabled_config.value = "true"
        else:
            enabled_config = SystemConfig(
                key="webhook_enabled",
                value="true",
                description="Webhook 是否启用"
            )
            db.add(enabled_config)

        # 保存事件类型
        events_config = db.query(SystemConfig).filter(SystemConfig.key == "webhook_events").first()
        if events_config:
            events_config.value = ",".join(request.events)
        else:
            events_config = SystemConfig(
                key="webhook_events",
                value=",".join(request.events),
                description="Webhook 订阅的事件类型"
            )
            db.add(events_config)

        db.commit()
        return {"status": "success", "message": "Webhook 配置已保存"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/config")
async def get_webhook_config_api(admin=Depends(get_current_admin_user)):
    """获取 Webhook 配置"""
    config = get_webhook_config()
    return {
        "status": "success",
        "data": {
            "enabled": config["enabled"],
            "url": config["url"],
            "events": config["events"]
        }
    }


@router.post("/test")
async def test_webhook(admin=Depends(get_current_admin_user)):
    """测试 Webhook 连接"""
    config = get_webhook_config()
    if not config["url"]:
        raise HTTPException(status_code=400, detail="请先配置 Webhook URL")

    from services.webhook import get_webhook_service
    webhook_service = get_webhook_service()

    result = await webhook_service.send_webhook(config["url"], "test", {
        "message": "这是一条测试消息",
        "admin": admin.username
    })

    if result["success"]:
        return {"status": "success", "message": "测试消息发送成功"}
    else:
        raise HTTPException(status_code=500, detail=result["message"])
