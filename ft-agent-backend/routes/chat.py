# -*- coding: utf-8 -*-
import json
import queue
import threading
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from core.database import SessionLocal, User, Subscription, UserTier, TokenAccount, TokenTransaction
from core.engine import run_agent, run_agent_stream, count_tokens
from routes.dependencies import get_current_user

router = APIRouter(prefix="", tags=["对话"])


class ChatRequest(BaseModel):
    message: str
    agent_type: Optional[str] = None
    user_id: str
    session_id: Optional[str] = None
    use_memory: bool = True
    conversation_history_limit: int = 10


def get_agent_type_by_user(db, user_id: str, fallback_agent_type: Optional[str] = None) -> str:
    """根据用户订阅等级获取 Agent 类型"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active"
    ).first()

    if subscription:
        tier = db.query(UserTier).filter(UserTier.id == subscription.tier_id).first()
        if tier and tier.agent_type:
            return tier.agent_type

    return fallback_agent_type or "tax_basic"


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, user: User = Depends(get_current_user)):
    """智能对话接口（根据用户订阅等级自动选用 Agent）"""
    try:
        db = SessionLocal()
        try:
            agent_type = get_agent_type_by_user(db, request.user_id, request.agent_type)
        finally:
            db.close()

        response = run_agent(
            user_input=request.message,
            agent_type=agent_type,
            user_id=request.user_id,
            session_id=request.session_id,
            use_memory=request.use_memory,
            conversation_history_limit=request.conversation_history_limit
        )
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/stream")
def test_stream():
    """测试流式输出"""
    import time

    def gen():
        for i in range(10):
            yield f"data: chunk {i}\n\n"
            time.sleep(0.1)
        yield "data: done\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, user: User = Depends(get_current_user)):
    """流式对话接口（SSE），实现打字机效果"""
    try:
        db = SessionLocal()
        try:
            agent_type = get_agent_type_by_user(db, request.user_id, request.agent_type)
        finally:
            db.close()

        result = run_agent_stream(
            user_input=request.message,
            agent_type=agent_type,
            user_id=request.user_id,
            session_id=request.session_id,
            use_memory=request.use_memory,
            conversation_history_limit=request.conversation_history_limit
        )

        if "error" in result:
            return {"status": "error", "data": {"error": result["error"], "token_insufficient": result.get("token_insufficient", False)}}

        input_tokens = result["input_tokens"]
        estimated_total = result["estimated_total"]
        tier_config = result["tier_config"]

        db = SessionLocal()
        try:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == request.user_id).first()
            if not account:
                account = TokenAccount(user_id=request.user_id, balance=0)
                db.add(account)
                db.flush()

            actual_prededuct = min(estimated_total, account.balance)
            if actual_prededuct > 0:
                account.balance -= actual_prededuct
                account.total_consumed += actual_prededuct

                transaction = TokenTransaction(
                    user_id=request.user_id,
                    transaction_type="consume",
                    amount=-actual_prededuct,
                    balance_after=account.balance,
                    description=f"对话预扣（{tier_config.get('name', '基础版')}）流式"
                )
                db.add(transaction)
            db.commit()
        finally:
            db.close()

        references = result["references"]
        memory_manager = result["memory_manager"]
        user_input = result["user_input"]
        agent_type = result["agent_type"]
        stream_yield = result["stream_yield"]

        def event_generator():
            """同步生成器 - 真正的流式传输"""
            full_response = ""

            q = queue.Queue()
            exception_holder = [None]

            def run_stream():
                try:
                    for content in stream_yield():
                        q.put(content)
                except Exception as e:
                    exception_holder[0] = e
                finally:
                    q.put(None)

            t = threading.Thread(target=run_stream)
            t.start()

            while True:
                chunk = q.get()
                if chunk is None:
                    break
                if exception_holder[0]:
                    raise exception_holder[0]
                full_response += chunk
                data = json.dumps({"content": chunk})
                yield f"data: {data}\n\n"

            t.join()

            output_tokens = count_tokens(full_response)
            actual_tokens = input_tokens + output_tokens
            diff = actual_prededuct - actual_tokens

            db = SessionLocal()
            try:
                account = db.query(TokenAccount).filter(TokenAccount.user_id == request.user_id).first()
                if account:
                    if diff > 0:
                        account.balance += diff
                        account.total_consumed -= diff
                        transaction = TokenTransaction(
                            user_id=request.user_id,
                            transaction_type="refund",
                            amount=diff,
                            balance_after=account.balance,
                            description=f"流式对话退款（预估-实际={diff}）"
                        )
                        db.add(transaction)
                    elif diff < 0:
                        actual_deduct = min(abs(diff), account.balance)
                        if actual_deduct > 0:
                            account.balance -= actual_deduct
                            account.total_consumed += actual_deduct
                            transaction = TokenTransaction(
                                user_id=request.user_id,
                                transaction_type="consume",
                                amount=-actual_deduct,
                                balance_after=account.balance,
                                description=f"流式对话补扣（实际-预估={abs(diff)}）"
                            )
                            db.add(transaction)
                    db.commit()
            finally:
                db.close()

            if memory_manager:
                memory_manager.add_message("user", user_input, agent_type)
                memory_manager.add_message("assistant", full_response, agent_type, references=references)

            finish_data = json.dumps({
                "type": "finish",
                "token_used": actual_tokens,
                "references": references
            })
            yield f"data: {finish_data}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
