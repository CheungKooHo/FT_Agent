import os
import tiktoken
from langchain_openai import ChatOpenAI
from core.database import SessionLocal, Agent, TokenAccount, TokenTransaction, Subscription, UserTier
from core.rag_engine import search_knowledge, search_knowledge_preview
from core.memory import MemoryManager
from core.tier_config import TIER_CONFIGS, DEFAULT_TIER
from typing import Optional


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    使用 tiktoken 计算文本的 token 数量
    """
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception:
        # 如果失败，估算（中文字符约 2 tokens/字符）
        return len(text) * 2


def count_messages_tokens(messages: list, model: str = "cl100k_base") -> int:
    """
    计算对话消息列表的总 token 数
    messages 格式: [{"role": "user", "content": "..."}, ...]
    """
    try:
        encoding = tiktoken.get_encoding(model)
        total = 0
        for msg in messages:
            # 每条消息有固定 overhead: role + content + 分隔符
            total += 3  # overhead per message
            total += len(encoding.encode(msg.get("content", "")))
        return total
    except Exception:
        # 估算
        return sum(len(m.get("content", "")) * 2 + 10 for m in messages)


def get_user_tier_config(user_id: str) -> dict:
    """
    获取用户当前 Tier 配置
    1. 检查用户是否有有效订阅
    2. 返回对应的 Tier 配置
    """
    db = SessionLocal()
    try:
        # 查询用户有效订阅
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).order_by(Subscription.end_date.desc()).first()

        if not subscription:
            # 无订阅，返回默认基础版
            return TIER_CONFIGS[DEFAULT_TIER].copy()

        tier = db.query(UserTier).filter(UserTier.id == subscription.tier_id).first()
        if not tier or not tier.is_active:
            return TIER_CONFIGS[DEFAULT_TIER].copy()

        tier_config = TIER_CONFIGS.get(tier.tier_code)
        if not tier_config:
            return TIER_CONFIGS[DEFAULT_TIER].copy()

        return tier_config.copy()
    finally:
        db.close()


def check_token_balance(user_id: str, required_tokens: int) -> tuple:
    """
    检查 Token 余额是否充足
    Returns: (success: bool, message: str)
    """
    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()

        # 如果没有账户，余额为0
        if not account:
            if required_tokens > 0:
                return False, "您的 Token 余额不足，请先充值"
            return True, "OK"

        # 检查余额
        if account.balance < required_tokens:
            return False, "您的 Token 余额不足，请先充值"

        return True, "OK"
    finally:
        db.close()


def consume_tokens(user_id: str, amount: int, description: str = "对话消耗") -> bool:
    """
    扣除指定数量的 Token
    """
    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()

        if not account:
            account = TokenAccount(user_id=user_id, balance=0)
            db.add(account)
            db.flush()

        account.balance -= amount
        account.total_consumed += amount

        transaction = TokenTransaction(
            user_id=user_id,
            transaction_type="consume",
            amount=-amount,
            balance_after=account.balance,
            description=description
        )
        db.add(transaction)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Token 扣除失败: {e}")
        return False
    finally:
        db.close()


def refund_tokens(user_id: str, amount: int, description: str = "Token 退款") -> bool:
    """
    退还 Token（用于实际用量小于估算的情况）
    """
    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()

        if not account:
            account = TokenAccount(user_id=user_id, balance=0)
            db.add(account)
            db.flush()

        account.balance += amount
        account.total_consumed -= amount  # 减少累计消耗

        transaction = TokenTransaction(
            user_id=user_id,
            transaction_type="refund",
            amount=amount,
            balance_after=account.balance,
            description=description
        )
        db.add(transaction)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Token 退款失败: {e}")
        return False
    finally:
        db.close()


def get_token_balance(user_id: str) -> int:
    """获取用户 Token 余额"""
    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
        return account.balance if account else 0
    finally:
        db.close()


def grant_free_token(user_id: str, amount: int = None) -> bool:
    """
    赠送免费 Token（用于新用户注册）
    """
    from core.tier_config import TIER_CONFIGS

    if amount is None:
        amount = TIER_CONFIGS["basic"]["monthly_token_quota"]

    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()

        if not account:
            account = TokenAccount(user_id=user_id, balance=0)
            db.add(account)
            db.flush()  # 确保账户被写入数据库

        account.balance += amount
        account.total_granted += amount

        transaction = TokenTransaction(
            user_id=user_id,
            transaction_type="grant",
            amount=amount,
            balance_after=account.balance,
            description=f"新用户注册赠送 {amount} Token"
        )
        db.add(transaction)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"赠送 Token 失败: {e}")
        return False
    finally:
        db.close()


def run_agent(
    user_input: str,
    agent_type: str,
    user_id: str,
    session_id: Optional[str] = None,
    use_memory: bool = True,
    conversation_history_limit: int = 10
):
    """
    核心调度引擎：
    1. 根据用户 Tier 获取对应的人设配置
    2. 从记忆系统获取对话历史和用户记忆
    3. 从 Qdrant 向量库检索相关知识片段 (RAG)
    4. 组装增强后的 Prompt 并调用大模型
    5. 保存对话到记忆系统
    6. 扣除 Token

    Args:
        user_input: 用户输入
        agent_type: agent 类型
        user_id: 用户ID
        session_id: 会话ID（可选）
        use_memory: 是否使用记忆系统
        conversation_history_limit: 对话历史条数限制
    """
    # --- 0. 获取用户 Tier 配置 ---
    tier_config = get_user_tier_config(user_id)

    # --- 2. 初始化记忆管理器 ---
    memory_manager = None
    conversation_history = []
    user_memory_summary = ""

    if use_memory:
        memory_manager = MemoryManager(user_id=user_id, session_id=session_id)

        # 获取对话历史
        conversation_history = memory_manager.get_conversation_history(
            agent_type=agent_type,
            limit=conversation_history_limit
        )

        # 获取用户长期记忆摘要
        user_memory_summary = memory_manager.get_memory_summary()

    # --- 3. 检索知识库 (RAG) ---
    context = ""
    references = []
    try:
        rag_results = search_knowledge(user_input, agent_type)
        print(f"===== RAG检索结果 =====")
        print(f"查询: {user_input}")
        print(f"Agent类型: {agent_type}")
        print(f"RAG结果长度: {len(rag_results)}")
        print(f"RAG结果内容: {rag_results[:200] if rag_results else '空'}...")
        print(f"========================")

        # 获取结构化引用（用于前端展示）
        preview_results = search_knowledge_preview(user_input, agent_type, top_k=5)
        references = preview_results.get("chunks", []) if preview_results else []

        context = rag_results if rag_results else "未找到相关政策背景知识。"
    except Exception as e:
        print(f"RAG 检索异常: {e}")
        context = "政策知识库暂不可用。"

    # --- 4. 构造增强 Prompt ---
    # 优先使用数据库中 Agent 配置的 prompt，其次用 tier_config 的
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.agent_type == agent_type, Agent.is_active == True).first()
        system_prompt = agent.prompt if agent else tier_config.get("system_prompt", TIER_CONFIGS[DEFAULT_TIER]["system_prompt"])
    finally:
        db.close()

    enhanced_prompt = f"""你是一个专业助手。以下是相关信息，请结合这些信息来回答用户的问题。

【参考资料】:
{context}

【你的专业人设】:
{system_prompt}
"""

    # 添加用户记忆（如果有）
    if user_memory_summary and user_memory_summary != "暂无用户记忆":
        enhanced_prompt += f"""

【用户记忆】:
{user_memory_summary}
（请在回答时考虑用户的背景和偏好）
"""

    # 构建消息列表
    messages = []
    messages.append({"role": "system", "content": enhanced_prompt})

    # 添加历史对话
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 添加当前用户问题
    messages.append({"role": "user", "content": user_input})

    # --- 5. 计算输入 token 数 ---
    input_tokens = count_messages_tokens(messages)

    # --- 5.1 检查 Token 余额（仅检查输入，预估输出）---
    # 保守估计：输出 ≈ 输入 * 1.2
    estimated_total = int(input_tokens * 2.2)
    success, msg = check_token_balance(user_id, estimated_total)
    if not success:
        return {"error": msg, "token_insufficient": True}

    # 获取 agent 配置以确定模型
    db = SessionLocal()
    try:
        config = db.query(Agent).filter(Agent.agent_type == agent_type).first()
        model_name = config.model if config else "deepseek-chat"
    finally:
        db.close()

    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE"),
        temperature=0.3
    )

    try:
        response = llm.invoke(messages)
        assistant_message = response.content

        # --- 6. 计算实际 token 用量 ---
        output_tokens = count_tokens(assistant_message)
        actual_tokens = input_tokens + output_tokens

        # 扣除实际用量（不允许变负数）
        db = SessionLocal()
        try:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
            if not account:
                account = TokenAccount(user_id=user_id, balance=0)
                db.add(account)
                db.flush()

            # 计算实际可扣除量（不超过余额）
            actual_deduct = min(actual_tokens, account.balance)
            if actual_deduct > 0:
                account.balance -= actual_deduct
                account.total_consumed += actual_deduct

                transaction = TokenTransaction(
                    user_id=user_id,
                    transaction_type="consume",
                    amount=-actual_deduct,
                    balance_after=account.balance,
                    description=f"对话消耗（{tier_config.get('name', '基础版')}）"
                )
                db.add(transaction)
            db.commit()
        finally:
            db.close()

        # 如果实际用量超过估算，多扣的部分记录但不显示给用户
        if actual_tokens > estimated_total:
            print(f"Warning: actual_tokens({actual_tokens}) > estimated({estimated_total})")

        # --- 7. 保存对话到记忆系统 ---
        if use_memory and memory_manager:
            memory_manager.add_message("user", user_input, agent_type)
            memory_manager.add_message("assistant", assistant_message, agent_type, references=references)

        return {
            "response": assistant_message,
            "token_used": actual_tokens,
            "tier": tier_config.get("name", "基础版"),
            "references": references
        }
    except Exception as e:
        return {"error": f"大模型调用失败: {str(e)}", "token_insufficient": False}
