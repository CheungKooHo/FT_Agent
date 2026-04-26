# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from sqlalchemy import func

from core.database import SessionLocal, User, AdminUser, Subscription, UserTier, TokenAccount, TokenTransaction, KnowledgeFile, ConversationHistory
from core.rag_engine import get_collection_stats
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin统计"])


@router.get("/stats/overview")
async def admin_get_overview(admin: AdminUser = Depends(get_current_admin_user)):
    """获取管理后台概览统计"""
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        total_admins = db.query(AdminUser).count()

        total_tokens = db.query(TokenAccount).all()
        total_balance = sum(a.balance for a in total_tokens)
        total_consumed = sum(a.total_consumed for a in total_tokens)
        total_purchased = sum(a.total_purchased for a in total_tokens)

        active_subs = db.query(Subscription).filter(Subscription.status == "active").count()
        total_subs = db.query(Subscription).count()

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        new_users_today = db.query(User).filter(User.created_at >= today_start).count()
        new_users_week = db.query(User).filter(User.created_at >= week_start).count()

        total_knowledge_files = db.query(KnowledgeFile).count()
        indexed_files = db.query(KnowledgeFile).filter(KnowledgeFile.is_indexed == True).count()

        agent_counts = {}
        for sub in db.query(Subscription).filter(Subscription.status == "active").all():
            tier_obj = db.query(UserTier).filter(UserTier.id == sub.tier_id).first()
            tier_name = tier_obj.tier_name if tier_obj else "未知"
            agent_counts[tier_name] = agent_counts.get(tier_name, 0) + 1

        token_accounts = db.query(TokenAccount).count()
        zero_balance_users = db.query(TokenAccount).filter(TokenAccount.balance == 0).count()

        tax_basic_stats = get_collection_stats("tax_basic")
        tax_pro_stats = get_collection_stats("tax_pro")

        return {
            "status": "success",
            "data": {
                "total_users": total_users,
                "total_admins": total_admins,
                "new_users_today": new_users_today,
                "new_users_week": new_users_week,
                "agent_distribution": agent_counts,
                "total_balance": total_balance,
                "total_consumed": total_consumed,
                "total_purchased": total_purchased,
                "token_accounts": token_accounts,
                "zero_balance_users": zero_balance_users,
                "active_subscriptions": active_subs,
                "total_subscriptions": total_subs,
                "total_knowledge_files": total_knowledge_files,
                "indexed_files": indexed_files,
                "tax_basic_vectors": tax_basic_stats.get("vectors_count", 0),
                "tax_pro_vectors": tax_pro_stats.get("vectors_count", 0)
            }
        }
    finally:
        db.close()


@router.get("/stats/token-usage")
async def admin_token_stats(admin: AdminUser = Depends(get_current_admin_user)):
    """Token 使用统计"""
    db = SessionLocal()
    try:
        all_accounts = db.query(TokenAccount).all()
        total_balance = sum(a.balance for a in all_accounts)
        total_consumed = sum(a.total_consumed for a in all_accounts)
        total_purchased = sum(a.total_purchased for a in all_accounts)
        zero_balance = sum(1 for a in all_accounts if a.balance == 0)

        tier_stats = {}
        for tier in db.query(UserTier).all():
            user_ids = [sub.user_id for sub in db.query(Subscription).filter(
                Subscription.tier_id == tier.id,
                Subscription.status == "active"
            ).all()]
            accounts = [a for a in all_accounts if a.user_id in user_ids]
            if accounts:
                tier_stats[tier.tier_name] = {
                    "count": len(accounts),
                    "balance": sum(a.balance for a in accounts),
                    "consumed": sum(a.total_consumed for a in accounts)
                }

        top_consumers = db.query(TokenAccount, User).join(
            User, TokenAccount.user_id == User.user_id
        ).order_by(TokenAccount.total_consumed.desc()).limit(20).all()

        recent_transactions = db.query(TokenTransaction, User).join(
            User, TokenTransaction.user_id == User.user_id
        ).order_by(TokenTransaction.created_at.desc()).limit(10).all()

        return {
            "status": "success",
            "data": {
                "summary": {
                    "total_balance": total_balance,
                    "total_consumed": total_consumed,
                    "total_purchased": total_purchased,
                    "total_accounts": len(all_accounts),
                    "zero_balance_accounts": zero_balance
                },
                "tier_stats": tier_stats,
                "top_consumers": [{
                    "username": u.username,
                    "user_id": acc.user_id,
                    "total_consumed": acc.total_consumed,
                    "total_purchased": acc.total_purchased,
                    "balance": acc.balance
                } for acc, u in top_consumers],
                "recent_transactions": [{
                    "username": u.username,
                    "user_id": trans.user_id,
                    "type": trans.transaction_type,
                    "amount": trans.amount,
                    "balance_after": trans.balance_after,
                    "description": trans.description,
                    "created_at": trans.created_at.isoformat()
                } for trans, u in recent_transactions]
            }
        }
    finally:
        db.close()


@router.get("/stats/conversation")
async def admin_conversation_stats(admin: AdminUser = Depends(get_current_admin_user)):
    """对话统计分析"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        total_conversations = db.query(ConversationHistory).count()
        total_users_with_chat = db.query(ConversationHistory.user_id).distinct().count()

        daily_stats = []
        for i in range(29, -1, -1):
            day = today_start - timedelta(days=i)
            next_day = day + timedelta(days=1)
            count = db.query(ConversationHistory).filter(
                ConversationHistory.created_at >= day,
                ConversationHistory.created_at < next_day
            ).count()
            daily_stats.append({
                "date": day.strftime("%Y-%m-%d"),
                "messages": count
            })

        daily_token_stats = []
        for i in range(29, -1, -1):
            day = today_start - timedelta(days=i)
            next_day = day + timedelta(days=1)
            consumed = db.query(TokenTransaction).filter(
                TokenTransaction.created_at >= day,
                TokenTransaction.created_at < next_day,
                TokenTransaction.transaction_type == "consume"
            ).all()
            total = sum(abs(t.amount) for t in consumed)
            daily_token_stats.append({
                "date": day.strftime("%Y-%m-%d"),
                "tokens": total
            })

        agent_stats = {}
        valid_agents = ['tax_basic', 'tax_pro']
        for agent_type in valid_agents:
            count = db.query(ConversationHistory).filter(
                ConversationHistory.agent_type == agent_type
            ).count()
            if count > 0:
                agent_stats[agent_type] = count

        today_messages = db.query(ConversationHistory).filter(
            ConversationHistory.created_at >= today_start
        ).count()
        week_messages = db.query(ConversationHistory).filter(
            ConversationHistory.created_at >= week_start
        ).count()
        month_messages = db.query(ConversationHistory).filter(
            ConversationHistory.created_at >= month_start
        ).count()

        active_users_7d = db.query(ConversationHistory.user_id).filter(
            ConversationHistory.created_at >= (now - timedelta(days=7))
        ).distinct().count()

        all_users = db.query(User).count()
        silent_users = all_users - total_users_with_chat

        avg_messages_per_user = round(total_conversations / total_users_with_chat, 1) if total_users_with_chat > 0 else 0

        sessions = db.query(ConversationHistory.session_id).distinct().count()
        avg_session_length = round(total_conversations / sessions, 1) if sessions > 0 else 0

        return {
            "status": "success",
            "data": {
                "summary": {
                    "total_conversations": total_conversations,
                    "total_users_with_chat": total_users_with_chat,
                    "active_users_7d": active_users_7d,
                    "silent_users": silent_users,
                    "total_users": all_users,
                    "avg_messages_per_user": avg_messages_per_user,
                    "avg_session_length": avg_session_length,
                    "total_sessions": sessions
                },
                "time_stats": {
                    "today_messages": today_messages,
                    "week_messages": week_messages,
                    "month_messages": month_messages
                },
                "daily_trend": daily_stats,
                "daily_token_trend": daily_token_stats,
                "agent_distribution": agent_stats
            }
        }
    finally:
        db.close()
