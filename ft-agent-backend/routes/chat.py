# -*- coding: utf-8 -*-
import json
import queue
import threading
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from core.database import SessionLocal, User, Subscription, UserTier, TokenAccount, TokenTransaction
from core.engine import run_agent, run_agent_stream, count_tokens, filter_basic_tier_response
from routes.dependencies import get_current_user

router = APIRouter(prefix="", tags=["对话"])


class ChatRequest(BaseModel):
    message: str
    agent_type: Optional[str] = None
    user_id: str
    session_id: Optional[str] = None
    use_memory: bool = True
    conversation_history_limit: int = 10
    trial_pro: bool = False  # 是否试用专业版


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
            # 处理专业版试用逻辑
            agent_type = get_agent_type_by_user(db, request.user_id, request.agent_type)
            if request.trial_pro and agent_type == "tax_basic":
                account = db.query(TokenAccount).filter(TokenAccount.user_id == request.user_id).first()
                if account and account.trial_pro_count > 0:
                    account.trial_pro_count -= 1
                    agent_type = "tax_pro"
                    db.commit()
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
                data = json.dumps({"content": chunk}, ensure_ascii=False)
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
                        actual_deduct = min(abs(diff), max(0, account.balance))
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
                memory_manager.close()

            # 基础版：流结束后不再追加提示，依赖 System Prompt 限制

            finish_data = json.dumps({
                "type": "finish",
                "token_used": actual_tokens,
                "references": references
            }, ensure_ascii=False)
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


def get_default_trial_count(db):
    """从系统配置获取默认试用次数"""
    from core.database import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.key == 'trial_pro_count').first()
    if config and config.value:
        try:
            return int(config.value)
        except ValueError:
            return 3
    return 3


@router.get("/user/trial-count")
async def get_trial_count(user: User = Depends(get_current_user)):
    """获取用户专业版试用剩余次数"""
    try:
        db = SessionLocal()
        try:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == user.user_id).first()
            default_count = get_default_trial_count(db)
            if not account:
                account = TokenAccount(user_id=user.user_id, balance=0, trial_pro_count=default_count)
                db.add(account)
                db.commit()
            return {"status": "success", "data": {"trial_pro_count": account.trial_pro_count, "default_count": default_count}}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-config/trial-pro-count")
async def get_trial_pro_count_config():
    """获取专业版试用次数配置（公开接口，无需admin）"""
    db = SessionLocal()
    try:
        default_count = get_default_trial_count(db)
        return {"status": "success", "data": {"trial_pro_count": default_count}}
    finally:
        db.close()


class RecommendedQuestionsRequest(BaseModel):
    last_user_message: str
    last_ai_response: str
    tier: str = "basic"


@router.post("/chat/recommended-questions")
async def get_recommended_questions(request: RecommendedQuestionsRequest, user: User = Depends(get_current_user)):
    """根据当前对话内容生成推荐的后续问题"""
    try:
        from core.engine import run_agent

        # 根据版本选择不同的提示词
        if request.tier == "pro":
            system_prompt = """你是一个财税专家的助手。根据用户和AI的对话内容，生成5个用户可能会问的后续问题。
要求：
1. 问题应该与对话内容紧密相关，是用户可能会关心的财税问题
2. 每次生成的问题应该有所不同，根据对话上下文定制
3. 问题要简洁明了，控制在20字以内
4. 只需要输出问题，不要其他解释
5. 用中文输出

格式：每行一个问题，共5行"""
        else:
            system_prompt = """你是一个财税政策助手。根据用户和AI的对话内容，生成5个用户可能会问的后续政策问题。
要求：
1. 问题应该与对话内容紧密相关，是用户可能会关心的政策问题
2. 每次生成的问题应该有所不同，根据对话上下文定制
3. 问题要简洁明了，控制在20字以内
4. 只需要输出问题，不要其他解释
5. 用中文输出

格式：每行一个问题，共5行"""

        response = run_agent(
            user_input=f"基于以下对话，生成5个后续问题：\n\n用户：{request.last_user_message}\n\nAI：{request.last_ai_response}",
            agent_type="tax_basic" if request.tier == "basic" else "tax_pro",
            user_id=user.user_id,
            use_memory=False,
            conversation_history_limit=0
        )

        # 解析返回的问题
        content = response.get("response", "")
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        # 过滤出真正的问题（包含问号或以？结尾）
        questions = []
        for line in lines:
            # 必须包含问号才是问题
            if "？" not in line and "?" not in line:
                continue
            # 清理可能的前缀编号
            clean_line = line.strip("。").strip()
            if clean_line.startswith(("1", "2", "3", "4", "5", "一、", "二、", "三、", "四、", "五、")):
                clean_line = clean_line.lstrip("12345一、二、三、四、五、.、 ")
            # 去掉 markdown 格式符号
            clean_line = clean_line.replace("**", "").strip()
            if clean_line:
                questions.append(clean_line)
            if len(questions) >= 5:
                break

        # 如果解析失败，使用默认问题
        if not questions:
            questions = [
                "企业所得税最新优惠政策有哪些?",
                "增值税专用发票和普通发票的区别",
                "个人所得税专项附加扣除标准",
                "公司报销哪些发票可以抵扣?",
                "小微企业税收优惠政策汇总"
            ]

        return {"status": "success", "data": {"questions": questions}}
    except Exception as e:
        # 出错时返回默认问题
        default_questions = [
            "企业所得税最新优惠政策有哪些?",
            "增值税专用发票和普通发票的区别",
            "个人所得税专项附加扣除标准",
            "公司报销哪些发票可以抵扣?",
            "小微企业税收优惠政策汇总"
        ]
        return {"status": "success", "data": {"questions": default_questions}}
