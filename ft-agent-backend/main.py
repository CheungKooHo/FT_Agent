# -*- coding: utf-8 -*-
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.database import init_db

init_db()

app = FastAPI(title="FT-Agent 财税智能平台")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class APIPrefixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            new_path = request.url.path[4:]
            request.scope["path"] = new_path
        response = await call_next(request)
        return response


app.add_middleware(APIPrefixMiddleware)

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

app.include_router(auth_router)
app.include_router(chat_router)
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


@app.get("/")
async def root():
    return {"message": "FT-Agent 财税智能平台 API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from tasks.scheduler import start_scheduler
    import threading

    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
