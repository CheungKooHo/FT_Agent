# -*- coding: utf-8 -*-
"""
支付配置模块
所有支付相关的密钥必须存储在环境变量中，不要硬编码
"""

import os

# ===== 支付宝配置 =====
ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_PRIVATE_KEY = os.getenv("ALIPAY_PRIVATE_KEY", "")
ALIPAY_PUBLIC_KEY = os.getenv("ALIPAY_PUBLIC_KEY", "")

# ===== 微信支付配置 =====
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_MCH_ID = os.getenv("WECHAT_MCH_ID", "")
WECHAT_API_KEY = os.getenv("WECHAT_API_KEY", "")

# ===== 支付回调地址 =====
PAYMENT_CALLBACK_URL = os.getenv("PAYMENT_CALLBACK_URL", "http://your-domain.com/payment/callback")

# ===== 沙箱环境（开发测试用） =====
ALIPAY_SANDBOX = os.getenv("ALIPAY_SANDBOX", "false").lower() == "true"
WECHAT_SANDBOX = os.getenv("WECHAT_SANDBOX", "false").lower() == "true"

# ===== 支付状态常量 =====
class PaymentStatus:
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

# ===== 支付渠道常量 =====
class PaymentChannel:
    ALIPAY = "alipay"
    WECHAT = "wechat"

# ===== 订单类型常量 =====
class OrderType:
    RECHARGE = "recharge"
    SUBSCRIPTION = "subscription"
