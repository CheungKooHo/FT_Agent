# -*- coding: utf-8 -*-
"""
邮件通知服务
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from dotenv import load_dotenv
load_dotenv()


class EmailService:
    """邮件服务"""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.enabled = os.getenv("SMTP_ENABLED", "false").lower() == "true"
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.username)
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送邮件"""
        if not self.enabled:
            print(f"[Email] 邮件服务未启用，无法发送邮件至 {to_email}")
            print(f"[Email] 主题: {subject}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())

            print(f"[Email] 邮件发送成功: {to_email} - {subject}")
            return True
        except Exception as e:
            print(f"[Email] 邮件发送失败: {e}")
            return False

    def send_subscription_expiring_notification(self, email: str, username: str, expire_date: str) -> bool:
        """发送订阅即将到期通知"""
        subject = "【FT-Agent】您的订阅即将到期"
        html = f"""
        <html>
        <body>
        <h2>亲爱的 {username}，您好！</h2>
        <p>您的 FT-Agent 订阅即将在 <strong>{expire_date}</strong> 到期。</p>
        <p>为避免服务中断，请及时续费。</p>
        <p>您可以登录 FT-Agent 平台进行续费操作。</p>
        <br/>
        <p>如有任何问题，请联系客服。</p>
        <br/>
        <p>FT-Agent 财税智能平台</p>
        </body>
        </html>
        """
        return self.send_email(email, subject, html)

    def send_payment_success_notification(self, email: str, username: str, amount: float, token_amount: int) -> bool:
        """发送支付成功通知"""
        subject = "【FT-Agent】支付成功通知"
        html = f"""
        <html>
        <body>
        <h2>亲爱的 {username}，您好！</h2>
        <p>您的充值已成功到账：</p>
        <ul>
            <li>充值金额：¥{amount:.2f}</li>
            <li>获得 Token：{token_amount:,}</li>
        </ul>
        <p>感谢您的支持！</p>
        <br/>
        <p>FT-Agent 财税智能平台</p>
        </body>
        </html>
        """
        return self.send_email(email, subject, html)


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """便捷函数：发送邮件"""
    return EmailService.get_instance().send_email(to_email, subject, html_content)
