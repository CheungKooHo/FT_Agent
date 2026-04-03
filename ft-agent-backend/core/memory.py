"""
记忆管理模块
负责对话历史和用户长期记忆的存储与检索
"""
from core.database import SessionLocal, ConversationHistory, UserMemory
from datetime import datetime
from typing import List, Dict, Optional


class MemoryManager:
    """记忆管理器"""

    def __init__(self, user_id: str, session_id: Optional[str] = None):
        """
        初始化记忆管理器

        Args:
            user_id: 用户ID
            session_id: 会话ID（可选，如果为None则使用user_id作为session_id）
        """
        self.user_id = user_id
        self.session_id = session_id or user_id
        self.db = SessionLocal()

    def __del__(self):
        """析构时关闭数据库连接"""
        self.db.close()

    # ==================== 对话历史管理 ====================

    def add_message(self, role: str, content: str, agent_type: str, references: Optional[List] = None):
        """
        添加一条对话消息到历史记录

        Args:
            role: "user" 或 "assistant"
            content: 消息内容
            agent_type: 使用的 agent 类型
            references: 引用知识库文档列表
        """
        import json
        message = ConversationHistory(
            user_id=self.user_id,
            session_id=self.session_id,
            agent_type=agent_type,
            role=role,
            content=content,
            references=json.dumps(references) if references else None
        )
        self.db.add(message)
        self.db.commit()

    def get_conversation_history(
        self,
        agent_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取对话历史

        Args:
            agent_type: 可选，只获取特定 agent 的对话历史
            limit: 返回最近的 N 条消息

        Returns:
            对话历史列表，格式: [{"role": "user", "content": "..."}, ...]
        """
        query = self.db.query(ConversationHistory).filter(
            ConversationHistory.user_id == self.user_id,
            ConversationHistory.session_id == self.session_id
        )

        if agent_type:
            query = query.filter(ConversationHistory.agent_type == agent_type)

        messages = query.order_by(
            ConversationHistory.created_at.desc()
        ).limit(limit).all()

        # 反转顺序，使其从旧到新
        import json
        result = []
        for msg in reversed(messages):
            item = {"role": msg.role, "content": msg.content}
            if msg.references:
                try:
                    item["references"] = json.loads(msg.references)
                except Exception:
                    item["references"] = []
            result.append(item)
        return result

    def clear_conversation_history(self, agent_type: Optional[str] = None):
        """
        清空对话历史

        Args:
            agent_type: 可选，只清空特定 agent 的对话历史
        """
        query = self.db.query(ConversationHistory).filter(
            ConversationHistory.user_id == self.user_id,
            ConversationHistory.session_id == self.session_id
        )

        if agent_type:
            query = query.filter(ConversationHistory.agent_type == agent_type)

        query.delete()
        self.db.commit()

    # ==================== 用户长期记忆管理 ====================

    def save_memory(
        self,
        key: str,
        value: str,
        memory_type: str = "fact",
        description: Optional[str] = None
    ):
        """
        保存或更新用户的长期记忆

        Args:
            key: 记忆的键（如 "occupation", "favorite_topic"）
            value: 记忆的值
            memory_type: 记忆类型（fact/preference/habit）
            description: 可选的描述信息
        """
        # 检查是否已存在
        existing = self.db.query(UserMemory).filter(
            UserMemory.user_id == self.user_id,
            UserMemory.key == key,
            UserMemory.memory_type == memory_type
        ).first()

        if existing:
            # 更新现有记忆
            existing.value = value
            existing.description = description
            existing.updated_at = datetime.utcnow()
        else:
            # 创建新记忆
            memory = UserMemory(
                user_id=self.user_id,
                memory_type=memory_type,
                key=key,
                value=value,
                description=description
            )
            self.db.add(memory)

        self.db.commit()

    def get_memory(
        self,
        key: str,
        memory_type: str = "fact"
    ) -> Optional[str]:
        """
        获取特定的用户记忆

        Args:
            key: 记忆的键
            memory_type: 记忆类型

        Returns:
            记忆的值，如果不存在则返回 None
        """
        memory = self.db.query(UserMemory).filter(
            UserMemory.user_id == self.user_id,
            UserMemory.key == key,
            UserMemory.memory_type == memory_type
        ).first()

        return memory.value if memory else None

    def get_all_memories(
        self,
        memory_type: Optional[str] = None
    ) -> List[Dict]:
        """
        获取用户的所有记忆

        Args:
            memory_type: 可选，只获取特定类型的记忆

        Returns:
            记忆列表，格式: [{"key": "...", "value": "...", "type": "...", "description": "..."}, ...]
        """
        query = self.db.query(UserMemory).filter(
            UserMemory.user_id == self.user_id
        )

        if memory_type:
            query = query.filter(UserMemory.memory_type == memory_type)

        memories = query.all()

        return [
            {
                "key": mem.key,
                "value": mem.value,
                "type": mem.memory_type,
                "description": mem.description
            }
            for mem in memories
        ]

    def delete_memory(self, key: str, memory_type: str = "fact"):
        """
        删除特定的用户记忆

        Args:
            key: 记忆的键
            memory_type: 记忆类型
        """
        self.db.query(UserMemory).filter(
            UserMemory.user_id == self.user_id,
            UserMemory.key == key,
            UserMemory.memory_type == memory_type
        ).delete()
        self.db.commit()

    def get_memory_summary(self) -> str:
        """
        获取用户记忆的文本摘要，用于传给 LLM

        Returns:
            格式化的记忆摘要文本
        """
        memories = self.get_all_memories()

        if not memories:
            return "暂无用户记忆"

        # 按类型分组
        grouped = {}
        for mem in memories:
            mem_type = mem["type"]
            if mem_type not in grouped:
                grouped[mem_type] = []
            grouped[mem_type].append(mem)

        # 构建摘要文本
        summary_parts = []

        type_names = {
            "fact": "用户信息",
            "preference": "用户偏好",
            "habit": "用户习惯"
        }

        for mem_type, items in grouped.items():
            type_name = type_names.get(mem_type, mem_type)
            summary_parts.append(f"\n【{type_name}】:")
            for item in items:
                desc = f" ({item['description']})" if item['description'] else ""
                summary_parts.append(f"- {item['key']}: {item['value']}{desc}")

        return "\n".join(summary_parts)
