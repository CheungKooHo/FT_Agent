# 用户管理系统使用指南

## 功能概述

完整的用户注册、登录和管理系统，支持：

1. **用户注册** - 创建新用户账号
2. **用户登录** - 验证用户身份
3. **用户信息查询** - 获取用户资料
4. **用户信息更新** - 修改昵称、邮箱等

## API 接口说明

### 1. 用户注册

**接口**: `POST /register`

**请求示例**:
```json
{
  "username": "zhangsan",
  "password": "password123",
  "email": "zhangsan@example.com",
  "nickname": "张三"
}
```

**参数说明**:
- `username`: 用户名（必填，唯一）
- `password`: 密码（必填，将被加密存储）
- `email`: 邮箱（可选，唯一）
- `nickname`: 昵称（可选，默认使用用户名）

**返回示例**:
```json
{
  "status": "success",
  "message": "注册成功",
  "data": {
    "user_id": "user_a1b2c3d4e5f6g7h8",
    "username": "zhangsan",
    "nickname": "张三",
    "email": "zhangsan@example.com",
    "created_at": "2024-02-24T10:30:00"
  }
}
```

**注意**:
- 返回的 `user_id` 是系统自动生成的唯一标识
- **请妥善保存 user_id，所有后续操作都需要使用它**

---

### 2. 用户登录

**接口**: `POST /login`

**请求示例**:
```json
{
  "username": "zhangsan",
  "password": "password123"
}
```

**返回示例**:
```json
{
  "status": "success",
  "message": "登录成功",
  "data": {
    "user_id": "user_a1b2c3d4e5f6g7h8",
    "username": "zhangsan",
    "nickname": "张三",
    "email": "zhangsan@example.com",
    "last_login": "2024-02-24T11:00:00"
  }
}
```

**用途**:
- 验证用户身份
- 获取用户的 user_id（用于后续 API 调用）

---

### 3. 获取用户信息

**接口**: `GET /user/{user_id}`

**请求示例**:
```
GET /user/user_a1b2c3d4e5f6g7h8
```

**返回示例**:
```json
{
  "status": "success",
  "data": {
    "user_id": "user_a1b2c3d4e5f6g7h8",
    "username": "zhangsan",
    "nickname": "张三",
    "email": "zhangsan@example.com",
    "is_active": true,
    "created_at": "2024-02-24T10:30:00",
    "last_login": "2024-02-24T11:00:00"
  }
}
```

---

### 4. 更新用户信息

**接口**: `PUT /user/{user_id}`

**请求示例**:
```json
{
  "nickname": "小张",
  "email": "newemail@example.com"
}
```

**参数说明**:
- 所有参数都是可选的
- 只更新提供的字段

---

## 完整使用流程示例

### 场景 1: 新用户注册并使用

```bash
# 1. 注册新用户
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "password": "password123",
    "email": "zhangsan@example.com",
    "nickname": "张三"
  }'

# 响应会返回 user_id，例如: user_a1b2c3d4e5f6g7h8

# 2. 使用 user_id 进行对话
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想了解增值税",
    "agent_type": "tax",
    "user_id": "user_a1b2c3d4e5f6g7h8",
    "use_memory": true
  }'

# 3. 保存用户记忆
curl -X POST "http://localhost:8000/memory" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_a1b2c3d4e5f6g7h8",
    "key": "occupation",
    "value": "会计师",
    "memory_type": "fact"
  }'
```

### 场景 2: 老用户登录

```bash
# 1. 登录获取 user_id
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "password": "password123"
  }'

# 响应会返回 user_id

# 2. 继续之前的对话（自动加载历史）
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "继续上次的话题",
    "agent_type": "tax",
    "user_id": "user_a1b2c3d4e5f6g7h8",
    "use_memory": true
  }'
```

---

## 数据库结构

### users 表
```
- id: 主键
- user_id: 用户唯一标识（自动生成）
- username: 用户名（唯一）
- password_hash: 密码哈希（SHA256）
- email: 邮箱（唯一）
- nickname: 昵称
- is_active: 是否激活
- created_at: 创建时间
- last_login: 最后登录时间
```

---

## 安全说明

1. **密码加密**: 使用 SHA256 哈希，不存储明文密码
2. **唯一性检查**: 用户名和邮箱都是唯一的
3. **账号状态**: 支持账号禁用功能（is_active）
4. **用户ID**: 使用随机生成的唯一标识，避免暴露顺序信息

---

## 注意事项

1. **user_id 是关键** - 所有记忆、对话都基于 user_id，请妥善保存
2. **username 不可修改** - 一旦注册就无法更改
3. **密码安全** - 建议使用强密码
4. **邮箱唯一** - 一个邮箱只能注册一个账号

---

## 常见问题

**Q: 忘记 user_id 怎么办？**
A: 使用 `/login` 接口重新登录，会返回 user_id

**Q: 可以修改用户名吗？**
A: 不可以，用户名作为唯一标识不能修改

**Q: 如何找回密码？**
A: 当前版本暂不支持密码找回，请妥善保管密码

**Q: user_id 的格式是什么？**
A: 格式为 `user_` 加上 16 位随机十六进制字符，例如 `user_a1b2c3d4e5f6g7h8`
