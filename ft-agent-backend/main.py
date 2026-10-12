# -*- coding: utf-8 -*-
import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.middleware.gzip import GZipMiddleware

from core.database import init_db

init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子：在此启动定时任务调度器

    放在 lifespan 里而不是 __main__ 块里，这样 `uvicorn main:app`（Docker 的启动方式）
    和 `python main.py` 两条路径都能生效。

    ENABLE_SCHEDULER 默认关闭：Docker 用 --workers 4 起多进程，每个进程都会执行
    lifespan，不加开关会导致同一批政策被并发抓 4 次。单进程部署（裸机/systemd）
    可设为 true 开启。
    """
    from tasks.scheduler import start_scheduler, stop_scheduler, _fetch_tax_policies_async

    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        start_scheduler()
        # 启动时立即执行一次抓取（后台运行，不阻塞 HTTP 服务器启动）
        print("[INFO] 启动时首次抓取政策（后台）...")
        asyncio.create_task(_fetch_tax_policies_async())
    else:
        print("[--] 定时任务调度器未启用（设置 ENABLE_SCHEDULER=true 开启）")

    yield

    stop_scheduler()


app = FastAPI(title="FT-Agent 财税智能平台", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


class APIPrefixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            new_path = request.url.path[4:]
            request.scope["path"] = new_path
        response = await call_next(request)
        return response


app.add_middleware(APIPrefixMiddleware)

from middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.knowledge import router as knowledge_router
from routes.token import router as token_router
from routes.subscription import router as subscription_router
from routes.payment import router as payment_router
from routes.memory import router as memory_router
from routes.setup import router as setup_router
from routes.notifications import router as notifications_router
from routes.admin.users import router as admin_users_router
from routes.admin.stats import router as admin_stats_router
from routes.admin.agents import router as admin_agents_router
from routes.admin.tiers import router as admin_tiers_router
from routes.admin.knowledge import router as admin_knowledge_router
from routes.admin.system import router as admin_system_router
from routes.admin.payment import router as admin_payment_router
from routes.admin.audit import router as admin_audit_router
from routes.admin.refund import router as admin_refund_router
from routes.refund import router as refund_router
from routes.feedback import router as feedback_router
from routes.favorites import router as favorites_router
from routes.admin.feedback import router as admin_feedback_router
from routes.admin.notifications import router as admin_notifications_router
from routes.webhook import router as webhook_router

app.include_router(chat_router)  # 先注册 chat，确保 /user/trial-count 被正确匹配
app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(token_router)
app.include_router(subscription_router)
app.include_router(payment_router)
app.include_router(memory_router)
app.include_router(setup_router)
app.include_router(notifications_router)
app.include_router(admin_users_router)
app.include_router(admin_stats_router)
app.include_router(admin_agents_router)
app.include_router(admin_tiers_router)
app.include_router(admin_knowledge_router)
app.include_router(admin_system_router)
app.include_router(admin_payment_router)
app.include_router(admin_audit_router)
app.include_router(admin_refund_router)
app.include_router(refund_router)
app.include_router(feedback_router)
app.include_router(favorites_router)
app.include_router(admin_feedback_router)
app.include_router(admin_notifications_router)
app.include_router(webhook_router)


@app.get("/")
async def root():
    return {"message": "FT-Agent 财税智能平台 API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
