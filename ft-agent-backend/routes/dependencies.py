# Shared dependencies for routes
from fastapi import Header, HTTPException, Depends
from typing import Optional

from core.database import SessionLocal, User, AdminUser
from core.security import verify_token


def get_current_user(authorization: str = Header(None)) -> User:
    """验证用户 JWT Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="无效的认证方案")
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的认证格式")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌已过期或无效")

    db = SessionLocal()
    try:
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")
        return user
    finally:
        db.close()


def get_current_admin_user(authorization: str = Header(None)) -> AdminUser:
    """验证 Admin JWT Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="无效的认证方案")
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的认证格式")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌已过期或无效")

    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == payload.get("sub")).first()
        if not admin or not admin.is_active:
            raise HTTPException(status_code=403, detail="无权限访问")
        return admin
    finally:
        db.close()
