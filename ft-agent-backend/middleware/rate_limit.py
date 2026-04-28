# -*- coding: utf-8 -*-
"""
API 限流中间件
基于 IP 和用户 ID 的请求限流
"""
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitStore:
    """简单的内存限流存储（生产环境应使用 Redis）"""

    def __init__(self):
        self.requests = defaultdict(list)  # key -> list of timestamps

    def add_request(self, key: str):
        """记录一次请求"""
        now = time.time()
        self.requests[key].append(now)

    def get_recent_count(self, key: str, window_seconds: int = 60) -> int:
        """获取指定时间窗口内的请求数"""
        now = time.time()
        cutoff = now - window_seconds
        timestamps = self.requests[key]
        # 清理过期记录
        self.requests[key] = [t for t in timestamps if t > cutoff]
        return len(self.requests[key])

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        """检查是否超过限制"""
        return self.get_recent_count(key, window_seconds) >= max_requests


# 全局限流存储
rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件
    配置项（通过环境变量）:
    - RATE_LIMIT_ENABLED: 是否启用限流 ("true"/"false")
    - RATE_LIMIT_PER_USER: 每个用户每分钟最大请求数（默认 60）
    - RATE_LIMIT_PER_IP: 每个 IP 每分钟最大请求数（默认 100）
    - RATE_LIMIT_WINDOW: 时间窗口秒数（默认 60）
    """

    def __init__(self, app):
        super().__init__(app)
        import os
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
        self.per_user = int(os.getenv("RATE_LIMIT_PER_USER", "60"))
        self.per_ip = int(os.getenv("RATE_LIMIT_PER_IP", "100"))
        self.window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    def get_user_id(self, request: Request) -> str:
        """从请求中获取用户标识"""
        # 尝试从 Authorization header 获取用户
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # 简单解析 JWT（不验证签名，只获取 user_id）
            try:
                import base64
                import json
                payload = token.split(".")[1]
                # 添加 padding
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += "=" * padding
                decoded = base64.urlsafe_b64decode(payload)
                data = json.loads(decoded)
                return data.get("sub", "") or "anonymous"
            except Exception:
                pass
        return "anonymous"

    def get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 优先使用 X-Forwarded-For 头（反向代理环境）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # 获取标识
        user_id = self.get_user_id(request)
        client_ip = self.get_client_ip(request)

        # 检查用户限流
        user_key = f"user:{user_id}"
        if rate_limit_store.is_rate_limited(user_key, self.per_user, self.window):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"请求过于频繁，请稍后再试（用户限流: {self.per_user}次/{self.window}秒）"
                }
            )

        # 检查 IP 限流
        ip_key = f"ip:{client_ip}"
        if rate_limit_store.is_rate_limited(ip_key, self.per_ip, self.window):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"请求过于频繁，请稍后再试（IP限流: {self.per_ip}次/{self.window}秒）"
                }
            )

        # 记录请求
        rate_limit_store.add_request(user_key)
        rate_limit_store.add_request(ip_key)

        return await call_next(request)
