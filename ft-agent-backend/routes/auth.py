# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from core.database import SessionLocal, User, AdminUser, Subscription, UserTier
from core.security import create_access_token
from core.tier_config import TIER_CONFIGS
from core.engine import grant_free_token
from routes.dependencies import get_current_user

router = APIRouter(prefix="", tags=["认证"])


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None


class EmailVerifyRequest(BaseModel):
    email: str


class EmailVerifyCodeRequest(BaseModel):
    email: str
    code: str


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register_user(request: UserRegisterRequest):
    """用户注册"""
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")

        if request.email:
            existing_email = db.query(User).filter(User.email == request.email).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已被注册")

        if request.phone:
            existing_phone = db.query(User).filter(User.phone == request.phone).first()
            if existing_phone:
                raise HTTPException(status_code=400, detail="手机号已被注册")

        user = User(
            user_id=User.generate_user_id(),
            username=request.username,
            email=request.email,
            phone=request.phone,
            nickname=request.nickname or request.username
        )
        user.set_password(request.password)

        db.add(user)
        db.commit()
        db.refresh(user)

        free_token_amount = TIER_CONFIGS["basic"]["monthly_token_quota"]
        grant_free_token(user.user_id, free_token_amount)

        basic_tier = db.query(UserTier).filter(UserTier.tier_code == "basic").first()
        if basic_tier:
            subscription = Subscription(
                user_id=user.user_id,
                tier_id=basic_tier.id,
                status="active",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365)
            )
            db.add(subscription)
            db.commit()

        access_token = create_access_token(data={"sub": user.user_id, "username": user.username})

        return {
            "status": "success",
            "message": "注册成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "free_token_granted": free_token_amount
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/send-email-verification")
async def send_email_verification(request: EmailVerifyRequest):
    """发送邮箱验证码"""
    import secrets

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if user and user.email_verified:
            return {"status": "success", "message": "邮箱已验证"}

        code = secrets.token_hex(4).upper()
        verification_code = f"{code}"

        if user:
            user.email_verification_code = verification_code
        else:
            return {"status": "error", "message": "邮箱未注册"}

        db.commit()

        # 发送邮件
        from services.email import EmailService
        email_service = EmailService.get_instance()
        subject = "【FT-Agent】邮箱验证码"
        html = f"""
        <html><body>
        <p>您好，您的邮箱验证码是：</p>
        <h2 style="color: #409eff; font-size: 32px; letter-spacing: 4px;">{code}</h2>
        <p>验证码 10 分钟内有效，请勿泄露给他人。</p>
        <br/>
        <p>FT-Agent 财税智能平台</p>
        </body></html>
        """
        email_service.send_email(request.email, subject, html)

        return {"status": "success", "message": "验证码已发送"}
    finally:
        db.close()


@router.post("/verify-email")
async def verify_email(request: EmailVerifyCodeRequest, user: User = Depends(get_current_user)):
    """验证邮箱验证码"""
    db = SessionLocal()
    try:
        if user.email != request.email:
            raise HTTPException(status_code=400, detail="邮箱不匹配")

        if user.email_verified:
            return {"status": "success", "message": "邮箱已验证"}

        if user.email_verification_code != request.code:
            raise HTTPException(status_code=400, detail="验证码错误")

        user.email_verified = True
        user.email_verification_code = None
        db.commit()

        return {"status": "success", "message": "邮箱验证成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/login")
async def login_user(request: UserLoginRequest):
    """用户登录"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == request.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.check_password(request.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        user.last_login = datetime.utcnow()
        db.commit()

        access_token = create_access_token(data={"sub": user.user_id, "username": user.username})

        return {
            "status": "success",
            "message": "登录成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "last_login": user.last_login.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Admin 管理员登录"""
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == request.username).first()
        if not admin:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not admin.check_password(request.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not admin.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        admin.last_login = datetime.utcnow()
        db.commit()

        access_token = create_access_token(data={"sub": admin.username, "role": admin.role})

        return {
            "status": "success",
            "message": "登录成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "username": admin.username,
                "role": admin.role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/user/{user_id}")
async def get_user_info(user_id: str):
    """获取用户信息"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "status": "success",
            "data": {
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "phone": user.phone,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "email_verified": user.email_verified,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/user/{user_id}")
async def update_user_info(user_id: str, request: UserUpdateRequest, user: User = Depends(get_current_user)):
    """更新用户信息"""
    db = SessionLocal()
    try:
        target_user = db.query(User).filter(User.user_id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if request.nickname is not None:
            target_user.nickname = request.nickname

        if request.email is not None:
            existing_email = db.query(User).filter(
                User.email == request.email,
                User.user_id != user_id
            ).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已被使用")
            target_user.email = request.email

        if request.phone is not None:
            existing_phone = db.query(User).filter(
                User.phone == request.phone,
                User.user_id != user_id
            ).first()
            if existing_phone:
                raise HTTPException(status_code=400, detail="手机号已被使用")
            target_user.phone = request.phone

        if request.avatar_url is not None:
            target_user.avatar_url = request.avatar_url

        if request.bio is not None:
            target_user.bio = request.bio

        db.commit()
        db.refresh(target_user)

        return {
            "status": "success",
            "message": "更新成功",
            "data": {
                "user_id": target_user.user_id,
                "username": target_user.username,
                "nickname": target_user.nickname,
                "email": target_user.email,
                "phone": target_user.phone,
                "avatar_url": target_user.avatar_url,
                "bio": target_user.bio
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
