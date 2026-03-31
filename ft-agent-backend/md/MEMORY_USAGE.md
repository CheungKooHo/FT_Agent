# 记忆系统使用指南

## 功能概述

本系统实现了完整的用户记忆功能，包括：

1. **对话历史记录** - 自动保存每次对话，支持多轮上下文
2. **用户长期记忆** - 存储用户的个人信息、偏好、习惯等
3. **按用户隔离** - 每个用户拥有独立的记忆空间

## API 接口说明

### 1. 智能对话（带记忆）

**接口**: `POST /chat`

**请求示例**:
```json
{
  "message": "什么是增值税？",
  "agent_type": "tax",
  "user_id": "user_123",
  "session_id": "session_001",
  "use_memory": true,
  "conversation_history_limit": 10
}
```

**参数说明**:
- `message`: 用户消息
- `agent_type`: 使用的 agent 类型（如 "tax"）
- `user_id`: 用户ID（**必填**）
- `session_id`: 会话ID（可选，不同会话可以有独立的对话历史）
- `use_memory`: 是否启用记忆功能（默认 true）
- `conversation_history_limit`: 载入的历史对话条数（默认 10）

**功能**:
- 自动载入对话历史，实现多轮对话
- 自动载入用户长期记忆，提供个性化回答
- 对话结束后自动保存到历史记录

---

### 2. 保存用户记忆

**接口**: `POST /memory`

**请求示例**:
```json
{
  "user_id": "user_123",
  "key": "occupation",
  "value": "会计师",
  "memory_type": "fact",
  "description": "用户职业信息"
}
```

**记忆类型**:
- `fact`: 用户事实信息（职业、年龄、所在地等）
- `preference`: 用户偏好（喜好、风格等）
- `habit`: 用户习惯（常问问题、使用习惯等）

---

### 3. 获取用户记忆

**接口**: `GET /memory/{user_id}?memory_type=fact`

**请求示例**:
```
GET /memory/user_123?memory_type=fact
```

**返回示例**:
```json
{
  "status": "success",
  "data": [
    {
      "key": "occupation",
      "value": "会计师",
      "type": "fact",
      "description": "用户职业信息"
    },
    {
      "key": "company_type",
      "value": "小微企业",
      "type": "fact",
      "description": "公司类型"
    }
  ]
}
```

---

### 4. 删除用户记忆

**接口**: `DELETE /memory?user_id=xxx&key=xxx&memory_type=fact`

**请求示例**:
```
DELETE /memory?user_id=user_123&key=occupation&memory_type=fact
```

---

### 5. 获取对话历史

**接口**: `GET /conversation_history/{user_id}`

**请求示例**:
```
GET /conversation_history/user_123?session_id=session_001&limit=20
```

**参数**:
- `session_id`: 可选，获取特定会话的历史
- `agent_type`: 可选，获取特定 agent 的对话
- `limit`: 返回的最大消息数（默认 50）

**返回示例**:
```json
{
  "status": "success",
  "data": [
    {
      "role": "user",
      "content": "什么是增值税？"
    },
    {
      "role": "assistant",
      "content": "增值税是一种流转税..."
    }
  ]
}
```

---

### 6. 清空对话历史

**接口**: `DELETE /conversation_history`

**请求示例**:
```
DELETE /conversation_history?user_id=user_123&session_id=session_001
```

---

## 使用场景示例

### 场景 1: 多轮对话

```python
# 第一轮对话
POST /chat
{
  "message": "我是一名会计师",
  "agent_type": "tax",
  "user_id": "user_123"
}

# 第二轮对话（自动记住上下文）
POST /chat
{
  "message": "我需要了解增值税的计算方法",
  "agent_type": "tax",
  "user_id": "user_123"
}
# Agent 会记住用户是会计师，提供更专业的回答
```

### 场景 2: 保存用户信息

```python
# 保存用户信息
POST /memory
{
  "user_id": "user_123",
  "key": "occupation",
  "value": "会计师",
  "memory_type": "fact"
}

POST /memory
{
  "user_id": "user_123",
  "key": "company_type",
  "value": "小微企业",
  "memory_type": "fact"
}

# 之后的对话会自动考虑这些信息
POST /chat
{
  "message": "我们公司如何享受税收优惠？",
  "agent_type": "tax",
  "user_id": "user_123"
}
# Agent 知道用户是小微企业的会计师，会提供针对性的建议
```

### 场景 3: 多会话管理

```python
# 工作相关的会话
POST /chat
{
  "message": "公司税务问题",
  "agent_type": "tax",
  "user_id": "user_123",
  "session_id": "work_session"
}

# 个人相关的会话
POST /chat
{
  "message": "个人所得税问题",
  "agent_type": "tax",
  "user_id": "user_123",
  "session_id": "personal_session"
}
# 两个会话的历史记录是分开的
```

---

## 数据库结构

### conversation_history 表
```
- id: 主键
- user_id: 用户ID
- session_id: 会话ID
- agent_type: Agent类型
- role: 角色（user/assistant）
- content: 消息内容
- created_at: 创建时间
```

### user_memory 表
```
- id: 主键
- user_id: 用户ID
- memory_type: 记忆类型（fact/preference/habit）
- key: 记忆键
- value: 记忆值
- description: 描述
- created_at: 创建时间
- updated_at: 更新时间
```

---

## 注意事项

1. **user_id 是必填的** - 所有记忆功能都基于 user_id
2. **session_id 是可选的** - 如果不提供，默认使用 user_id 作为 session_id
3. **记忆会影响 LLM 回答** - 保存的用户记忆会作为上下文传给模型
4. **对话历史有限制** - 默认只载入最近 10 条，可通过参数调整
5. **记忆类型建议** - 使用统一的 memory_type 便于管理和检索

---

## 测试建议

1. 先创建一个测试用户，保存一些记忆
2. 进行多轮对话，观察上下文是否正确
3. 查询对话历史，确认记录完整
4. 测试不同会话的隔离性
