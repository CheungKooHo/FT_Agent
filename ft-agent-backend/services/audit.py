# -*- coding: utf-8 -*-
"""
审计日志服务
"""
import json
from datetime import datetime
from typing import Optional


def create_audit_log(
    db,
    user_id: str,
    username: str,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """创建审计日志（内部函数）"""
    from core.database import AuditLog

    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    return log
