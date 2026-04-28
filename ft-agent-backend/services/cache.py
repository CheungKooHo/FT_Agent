# -*- coding: utf-8 -*-
"""
Redis 缓存服务
提供用户会话缓存和 Token 余额缓存
"""

import os
import json
import hashlib
from typing import Optional, Any
import redis


class RedisCache:
    """Redis 缓存服务"""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                self._client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3
                )
                # 测试连接
                self._client.ping()
                print(f"[OK] Redis 连接成功: {redis_url}")
            except redis.ConnectionError:
                print(f"[WARN] Redis 连接失败，使用内存缓存: {redis_url}")
                self._client = None

    @property
    def enabled(self) -> bool:
        """Redis 是否可用"""
        return self._client is not None

    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self.enabled:
            return None
        try:
            return self._client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """设置缓存值，expire 为过期时间（秒）"""
        if not self.enabled:
            return False
        try:
            self._client.setex(key, expire, value)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.enabled:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception:
            return False

    def get_json(self, key: str) -> Optional[Any]:
        """获取 JSON 缓存"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except Exception:
                return None
        return None

    def set_json(self, key: str, value: Any, expire: int = 3600) -> bool:
        """设置 JSON 缓存"""
        try:
            return self.set(key, json.dumps(value), expire)
        except Exception:
            return False


# 便捷函数
def get_cache() -> RedisCache:
    return RedisCache()


# Token 余额缓存
def cache_token_balance(user_id: str, balance: int, expire: int = 300) -> bool:
    """缓存用户 Token 余额，5 分钟过期"""
    cache = get_cache()
    return cache.set_json(f"token_balance:{user_id}", {"balance": balance, "updated_at": str(int(__import__("time").time()))}, expire)


def get_cached_token_balance(user_id: str) -> Optional[int]:
    """获取缓存的用户 Token 余额"""
    cache = get_cache()
    data = cache.get_json(f"token_balance:{user_id}")
    if data:
        return data.get("balance")
    return None


def invalidate_token_balance(user_id: str) -> bool:
    """使 Token 余额缓存失效"""
    cache = get_cache()
    return cache.delete(f"token_balance:{user_id}")


# 用户会话缓存
def cache_user_session(user_id: str, session_id: str, data: dict, expire: int = 1800) -> bool:
    """缓存用户会话数据，30 分钟过期"""
    cache = get_cache()
    return cache.set_json(f"session:{user_id}:{session_id}", data, expire)


def get_cached_user_session(user_id: str, session_id: str) -> Optional[dict]:
    """获取缓存的用户会话"""
    cache = get_cache()
    return cache.get_json(f"session:{user_id}:{session_id}")


def invalidate_user_session(user_id: str, session_id: str) -> bool:
    """使用户会话缓存失效"""
    cache = get_cache()
    return cache.delete(f"session:{user_id}:{session_id}")


# API 限流缓存
def check_rate_limit(key: str, limit: int, window: int = 60) -> tuple:
    """
    检查限流
    Returns: (allowed: bool, remaining: int, reset_at: int)
    """
    cache = get_cache()
    if not cache.enabled:
        return True, limit, 0

    try:
        r = cache._client
        current = r.get(key)
        if current is None:
            r.setex(key, window, 1)
            return True, limit - 1, window

        current = int(current)
        if current >= limit:
            ttl = r.ttl(key)
            return False, 0, ttl

        r.incr(key)
        ttl = r.ttl(key)
        return True, limit - current - 1, ttl
    except Exception:
        return True, limit, 0


# RAG 检索缓存
def cache_rag_search(query: str, collection: str, result: str, expire: int = 3600) -> bool:
    """缓存 RAG 检索结果，1 小时过期"""
    cache = get_cache()
    key = f"rag:{collection}:{hashlib.md5(query.encode()).hexdigest()}"
    return cache.set_json(key, {"result": result, "query": query}, expire)


def get_cached_rag_search(query: str, collection: str) -> Optional[str]:
    """获取缓存的 RAG 检索结果"""
    cache = get_cache()
    key = f"rag:{collection}:{hashlib.md5(query.encode()).hexdigest()}"
    data = cache.get_json(key)
    if data:
        return data.get("result")
    return None


def invalidate_rag_cache(collection: str = None) -> bool:
    """使 RAG 缓存失效"""
    cache = get_cache()
    if not cache.enabled:
        return False

    try:
        r = cache._client
        if collection:
            # 只删除指定 collection 的缓存
            pattern = f"rag:{collection}:*"
        else:
            # 删除所有 RAG 缓存
            pattern = "rag:*"

        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
        return True
    except Exception:
        return False
