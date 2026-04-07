from dotenv import load_dotenv

# 必须在最开始加载环境变量，确保 HF_ENDPOINT 等配置生效
load_dotenv()

import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import shutil
import json
from pathlib import Path
from core.engine import run_agent, grant_free_token, get_token_balance
from core.database import init_db, SessionLocal, Agent, User, TokenAccount, TokenTransaction, Subscription, UserTier, AdminUser, SystemConfig, UserTierRelation, KnowledgeFile, ConversationHistory
from sqlalchemy import func
from core.rag_engine import upload_and_index_pdf, search_knowledge_preview, get_collection_stats, get_file_chunks, delete_from_vectorstore
from core.memory import MemoryManager
from core.security import create_access_token, verify_token
from core.tier_config import TIER_CONFIGS, DEFAULT_TIER, TOKEN_PRICE_PER_MILLION

# 启动时创建数据库表
init_db()

app = FastAPI(title="FT-Agent 财税智能平台")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 前缀中间件 - 移除 /api 前缀以便与前端代理配合
class APIPrefixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            # 移除 /api 前缀
            new_path = request.url.path[4:]  # 去掉 "/api"
            request.scope["path"] = new_path
        response = await call_next(request)
        return response

app.add_middleware(APIPrefixMiddleware)

# 创建上传目录
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ==================== 认证相关函数 ====================

def get_current_user(authorization: str = Header(None)):
    """验证用户 JWT Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="无效的认证方案")
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的认证格式")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌已过期或无效")

    db = SessionLocal()
    try:
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")
        return user
    finally:
        db.close()

# ==================== 用户管理接口 ====================

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

@app.post("/register")
async def register_user(request: UserRegisterRequest):
    """
    用户注册

    请求示例:
    {
        "username": "zhangsan",
        "password": "password123",
        "email": "zhangsan@example.com",
        "nickname": "张三"
    }
    """
    db = SessionLocal()
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 检查邮箱是否已存在
        if request.email:
            existing_email = db.query(User).filter(User.email == request.email).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已被注册")

        # 检查手机号是否已存在
        if request.phone:
            existing_phone = db.query(User).filter(User.phone == request.phone).first()
            if existing_phone:
                raise HTTPException(status_code=400, detail="手机号已被注册")

        # 创建新用户
        user = User(
            user_id=User.generate_user_id(),
            username=request.username,
            email=request.email,
            phone=request.phone,
            nickname=request.nickname or request.username
        )
        user.set_password(request.password)

        db.add(user)
        db.commit()
        db.refresh(user)

        # 赠送新用户免费 Token（基础版1个月配额）
        free_token_amount = TIER_CONFIGS["basic"]["monthly_token_quota"]
        grant_free_token(user.user_id, free_token_amount)

        # 自动创建基础版订阅
        basic_tier = db.query(UserTier).filter(UserTier.tier_code == "basic").first()
        if basic_tier:
            subscription = Subscription(
                user_id=user.user_id,
                tier_id=basic_tier.id,
                status="active",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365)  # 基础版1年
            )
            db.add(subscription)
            db.commit()

        # 生成 JWT token
        access_token = create_access_token(data={"sub": user.user_id, "username": user.username})

        return {
            "status": "success",
            "message": "注册成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "free_token_granted": free_token_amount
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/login")
async def login_user(request: UserLoginRequest):
    """
    用户登录

    请求示例:
    {
        "username": "zhangsan",
        "password": "password123"
    }
    """
    db = SessionLocal()
    try:
        # 查找用户
        user = db.query(User).filter(User.username == request.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 验证密码
        if not user.check_password(request.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 检查是否激活
        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()

        # 生成 JWT token
        access_token = create_access_token(data={"sub": user.user_id, "username": user.username})

        return {
            "status": "success",
            "message": "登录成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "last_login": user.last_login.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ==================== Admin 登录接口 ====================

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@app.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """
    Admin 管理员登录
    """
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == request.username).first()
        if not admin:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not admin.check_password(request.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not admin.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        admin.last_login = datetime.utcnow()
        db.commit()

        access_token = create_access_token(data={"sub": admin.username, "role": admin.role})

        return {
            "status": "success",
            "message": "登录成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "username": admin.username,
                "role": admin.role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/user/{user_id}")
async def get_user_info(user_id: str):
    """
    获取用户信息

    参数:
    - user_id: 用户ID
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "status": "success",
            "data": {
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.put("/user/{user_id}")
async def update_user_info(user_id: str, request: UserUpdateRequest):
    """
    更新用户信息

    请求示例:
    {
        "nickname": "新昵称",
        "email": "newemail@example.com"
    }
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 更新信息
        if request.nickname is not None:
            user.nickname = request.nickname

        if request.email is not None:
            # 检查邮箱是否已被其他用户使用
            existing_email = db.query(User).filter(
                User.email == request.email,
                User.user_id != user_id
            ).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已被使用")
            user.email = request.email

        if request.phone is not None:
            # 检查手机号是否已被其他用户使用
            existing_phone = db.query(User).filter(
                User.phone == request.phone,
                User.user_id != user_id
            ).first()
            if existing_phone:
                raise HTTPException(status_code=400, detail="手机号已被使用")
            user.phone = request.phone

        db.commit()
        db.refresh(user)

        return {
            "status": "success",
            "message": "更新成功",
            "data": {
                "user_id": user.user_id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ==================== RAG 相关接口 ====================

@app.post("/upload_file")
async def upload_file(
    agent_type: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    上传 PDF 文件到知识库

    参数:
    - agent_type: Agent 类型
    - file: PDF 文件

    返回:
    - status: 处理状态
    - filename: 保存的文件名
    """
    # 检查文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()

    file_size = file_path.stat().st_size

    # 记录到数据库
    db = SessionLocal()
    try:
        # 检查同名文件是否已有记录，有则清理旧向量避免重复
        existing = db.query(KnowledgeFile).filter(
            KnowledgeFile.user_id == user.user_id,
            KnowledgeFile.original_filename == file.filename
        ).first()
        if existing and existing.doc_id:
            delete_from_vectorstore(existing.doc_id, agent_type)

        kf = KnowledgeFile(
            user_id=user.user_id,
            filename=safe_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type="pdf",
            agent_type=agent_type,
            is_indexed=False
        )
        db.add(kf)
        db.commit()
    finally:
        db.close()

    # 处理文件并索引到向量库
    try:
        result = upload_and_index_pdf(str(file_path), agent_type)

        # 更新索引状态和doc_id
        db = SessionLocal()
        try:
            kf = db.query(KnowledgeFile).filter(KnowledgeFile.filename == safe_filename).first()
            if kf:
                kf.is_indexed = True
                kf.doc_id = result.get("doc_id")
                kf.chunk_count = result.get("chunks", 0)
                db.commit()
        finally:
            db.close()

        return {
            "status": "success",
            "message": "文档处理完成",
            "filename": safe_filename,
            "file_path": str(file_path),
            "doc_id": result.get("doc_id"),
            "chunks": result.get("chunks", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


# ==================== 知识库管理接口 ====================

@app.get("/knowledge/files")
async def list_knowledge_files(user: User = Depends(get_current_user)):
    """
    获取知识库文件列表（包含索引状态和切片数）
    """
    db = SessionLocal()
    try:
        files = db.query(KnowledgeFile).filter(
            KnowledgeFile.user_id == user.user_id
        ).order_by(KnowledgeFile.created_at.desc()).all()

        # 获取各collection的统计
        collections = {}
        for agent_type in ["tax_basic", "tax_pro"]:
            stats = get_collection_stats(agent_type)
            collections[agent_type] = stats.get("points_count", 0)

        return {
            "status": "success",
            "files": [{
                "filename": f.filename,
                "original_filename": f.original_filename,
                "size": f.file_size,
                "agent_type": f.agent_type,
                "doc_id": f.doc_id,
                "chunk_count": f.chunk_count,
                "is_indexed": f.is_indexed,
                "created_at": f.created_at.isoformat()
            } for f in files],
            "collections": collections
        }
    finally:
        db.close()


@app.delete("/knowledge/files/{filename}")
async def delete_knowledge_file(
    filename: str,
    user: User = Depends(get_current_user)
):
    """
    删除知识库文件（从数据库删除，向量库标记删除）
    """
    db = SessionLocal()
    try:
        kf = db.query(KnowledgeFile).filter(
            KnowledgeFile.filename == filename,
            KnowledgeFile.user_id == user.user_id
        ).first()

        if not kf:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 删除物理文件（仅用户自己上传的文件有物理文件，引用记录的file_path为None）
        try:
            if kf.file_path and os.path.exists(kf.file_path):
                os.remove(kf.file_path)
        except Exception:
            pass

        # 从向量库删除（仅admin文件是权威来源，用户引用共享同一个doc_id不能删向量）
        if kf.user_id == "admin" and kf.agent_type and kf.doc_id:
            try:
                delete_from_vectorstore(kf.agent_type, kf.doc_id)
            except Exception as e:
                print(f"向量库删除失败: {e}")

        # 从数据库删除
        db.delete(kf)
        db.commit()

        return {
            "status": "success",
            "message": "文件已删除"
        }
    finally:
        db.close()


@app.get("/knowledge/files/{filename}/chunks")
async def get_knowledge_file_chunks(
    filename: str,
    user: User = Depends(get_current_user)
):
    """
    获取指定知识库文件的切片列表
    """
    db = SessionLocal()
    try:
        kf = db.query(KnowledgeFile).filter(
            KnowledgeFile.filename == filename,
            KnowledgeFile.user_id == user.user_id
        ).first()

        if not kf:
            raise HTTPException(status_code=404, detail="文件不存在")

        if not kf.doc_id or not kf.agent_type:
            return {"status": "success", "chunks": [], "total": 0, "message": "文件未索引"}

        result = get_file_chunks(kf.agent_type, kf.doc_id)
        return result
    finally:
        db.close()


@app.post("/knowledge/save-reference")
async def save_reference_document(
    doc_id: str,
    source: str,
    agent_type: str = "tax_basic",
    user: User = Depends(get_current_user)
):
    """
    将对话中引用的文档保存到用户知识库
    不复制文件，只创建引用记录，用户共享平台的同一个 doc_id
    """
    db = SessionLocal()
    try:
        # 找到源文件记录（平台公共文件）
        source_file = db.query(KnowledgeFile).filter(
            KnowledgeFile.doc_id == doc_id,
            KnowledgeFile.agent_type == agent_type
        ).first()

        if not source_file:
            raise HTTPException(status_code=404, detail="引用的文档不存在")

        # 检查用户是否已保存过该 doc_id
        existing = db.query(KnowledgeFile).filter(
            KnowledgeFile.user_id == user.user_id,
            KnowledgeFile.doc_id == doc_id
        ).first()
        if existing:
            return {
                "status": "success",
                "message": "文档已在知识库中",
                "filename": existing.original_filename,
                "doc_id": existing.doc_id
            }

        # 创建用户引用记录（指向同一个 doc_id，不复制文件）
        kf = KnowledgeFile(
            user_id=user.user_id,
            filename=source_file.filename,
            original_filename=source_file.original_filename,
            file_path=None,  # 物理文件归 admin 所有，用户不复制
            file_size=source_file.file_size,
            file_type="pdf",
            agent_type=agent_type,
            is_indexed=True,
            doc_id=doc_id,
            chunk_count=source_file.chunk_count
        )
        db.add(kf)
        db.commit()

        return {
            "status": "success",
            "message": "文档已保存到知识库",
            "filename": safe_filename,
            "doc_id": result.get("doc_id"),
            "chunks": result.get("chunks", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")
    finally:
        db.close()


@app.get("/knowledge/search_preview")
async def preview_knowledge_search(
    query: str,
    agent_type: str = "tax_basic",
    top_k: int = 5,
    user: User = Depends(get_current_user)
):
    """
    预览知识库搜索结果（测试检索效果）
    """
    result = search_knowledge_preview(query, agent_type, top_k)
    return result


@app.get("/knowledge/stats")
async def get_knowledge_stats(
    agent_type: str = "tax_basic",
    user: User = Depends(get_current_user)
):
    """
    获取知识库统计信息
    """
    stats = get_collection_stats(agent_type)
    return stats


# ==================== 对话接口 ====================

class ChatRequest(BaseModel):
    message: str
    agent_type: Optional[str] = None             # 已废弃，由订阅等级自动决定
    user_id: str                                # 必填：用户ID
    session_id: Optional[str] = None            # 可选：会话ID
    use_memory: bool = True                     # 是否使用记忆系统
    conversation_history_limit: int = 10        # 对话历史条数限制

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, user: User = Depends(get_current_user)):
    """
    智能对话接口（根据用户订阅等级自动选用对应 Agent）

    请求示例:
    {
        "message": "什么是增值税？",
        "user_id": "user_123",
        "session_id": "session_001",  // 可选
        "use_memory": true,
        "conversation_history_limit": 10
    }
    """
    try:
        # 根据用户订阅等级自动选用 Agent
        db = SessionLocal()
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == request.user_id,
                Subscription.status == "active"
            ).first()

            if subscription:
                tier = db.query(UserTier).filter(UserTier.id == subscription.tier_id).first()
                if tier and tier.agent_type:
                    agent_type = tier.agent_type
                else:
                    agent_type = request.agent_type  # fallback
            else:
                # 未订阅用户默认使用 basic
                agent_type = "tax_basic"
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

# ==================== Agent 配置接口 ====================

class SetupAgentRequest(BaseModel):
    name: str
    agent_type: str
    prompt: str

@app.post("/setup_agent")
async def setup_agent(request: SetupAgentRequest):
    """创建或配置 Agent"""
    db = SessionLocal()
    new_agent = Agent(name=request.name, agent_type=request.agent_type, prompt=request.prompt)
    db.add(new_agent)
    db.commit()
    db.close()
    return {"message": f"Agent {request.name} created!"}

# ==================== 记忆管理接口 ====================

class MemorySaveRequest(BaseModel):
    user_id: str
    key: str
    value: str
    memory_type: str = "fact"  # fact/preference/habit
    description: Optional[str] = None

@app.post("/memory")
async def save_user_memory(request: MemorySaveRequest, user: User = Depends(get_current_user)):
    """
    保存用户长期记忆

    请求示例:
    {
        "user_id": "user_123",
        "key": "occupation",
        "value": "会计师",
        "memory_type": "fact",
        "description": "用户职业"
    }
    """
    if request.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=request.user_id)
        memory_manager.save_memory(
            key=request.key,
            value=request.value,
            memory_type=request.memory_type,
            description=request.description
        )
        return {"status": "success", "message": "记忆已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{user_id}")
async def get_user_memories(
    user_id: str,
    memory_type: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    获取用户的所有记忆

    参数:
    - user_id: 用户ID
    - memory_type: 可选，记忆类型（fact/preference/habit）
    """
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id)
        memories = memory_manager.get_all_memories(memory_type=memory_type)
        return {"status": "success", "data": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory")
async def delete_user_memory(
    user_id: str,
    key: str,
    memory_type: str = "fact",
    user: User = Depends(get_current_user)
):
    """删除特定的用户记忆"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id)
        memory_manager.delete_memory(key=key, memory_type=memory_type)
        return {"status": "success", "message": "记忆已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation_history/{user_id}")
async def get_conversation_history(
    user_id: str,
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(get_current_user)
):
    """
    获取对话历史

    参数:
    - user_id: 用户ID
    - session_id: 可选，会话ID
    - agent_type: 可选，agent类型
    - limit: 返回的最大消息数
    """
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id, session_id=session_id)
        history = memory_manager.get_conversation_history(
            agent_type=agent_type,
            limit=limit
        )
        return {"status": "success", "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversation_history")
async def clear_conversation_history(
    user_id: str,
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """清空对话历史"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    try:
        memory_manager = MemoryManager(user_id=user_id, session_id=session_id)
        memory_manager.clear_conversation_history(agent_type=agent_type)
        return {"status": "success", "message": "对话历史已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Token 相关接口 ====================

@app.get("/token/balance")
async def get_token_balance_endpoint(user_id: str, user: User = Depends(get_current_user)):
    """获取用户 Token 余额"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
        if not account:
            return {
                "status": "success",
                "data": {
                    "balance": 0,
                    "total_purchased": 0,
                    "total_consumed": 0,
                    "total_granted": 0
                }
            }
        return {
            "status": "success",
            "data": {
                "balance": account.balance,
                "total_purchased": account.total_purchased,
                "total_consumed": account.total_consumed,
                "total_granted": account.total_granted
            }
        }
    finally:
        db.close()


@app.get("/token/transactions")
async def get_token_transactions(user_id: str, limit: int = 50, user: User = Depends(get_current_user)):
    """获取 Token 交易记录"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    db = SessionLocal()
    try:
        transactions = db.query(TokenTransaction).filter(
            TokenTransaction.user_id == user_id
        ).order_by(TokenTransaction.created_at.desc()).limit(limit).all()

        return {
            "status": "success",
            "data": [{
                "type": t.transaction_type,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            } for t in transactions]
        }
    finally:
        db.close()


@app.post("/token/recharge")
async def recharge_token(user_id: str, amount: int, user: User = Depends(get_current_user)):
    """Token 充值（模拟）"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限操作")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="充值数量必须大于0")

    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
        if not account:
            account = TokenAccount(user_id=user_id, balance=0)
            db.add(account)
            db.flush()

        account.balance += amount
        account.total_purchased += amount

        transaction = TokenTransaction(
            user_id=user_id,
            transaction_type="purchase",
            amount=amount,
            balance_after=account.balance,
            description=f"充值 {amount} Token"
        )
        db.add(transaction)
        db.commit()

        return {
            "status": "success",
            "message": "充值成功",
            "data": {"balance": account.balance}
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/token/price")
async def get_token_price():
    """获取Token价格"""
    return {
        "status": "success",
        "data": {
            "price_per_million": TOKEN_PRICE_PER_MILLION,  # 每百万Token价格（分）
            "price_yuan": TOKEN_PRICE_PER_MILLION / 100  # 每百万Token价格（元）
        }
    }


# ==================== 订阅相关接口 ====================

@app.get("/subscription")
async def get_subscription(user_id: str, user: User = Depends(get_current_user)):
    """获取当前订阅信息"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限访问")
    db = SessionLocal()
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).first()

        if not subscription:
            # 获取用户 Token 余额判断是否可使用基础版
            account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
            return {
                "status": "success",
                "data": {
                    "tier": "basic",
                    "tier_name": "基础版",
                    "status": "available",
                    "has_token": account.balance > 0 if account else False,
                    "token_balance": account.balance if account else 0
                }
            }

        tier = db.query(UserTier).filter(UserTier.id == subscription.tier_id).first()

        return {
            "status": "success",
            "data": {
                "tier": tier.tier_code if tier else "basic",
                "tier_name": tier.tier_name if tier else "基础版",
                "status": subscription.status,
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat(),
                "auto_renew": subscription.auto_renew
            }
        }
    finally:
        db.close()


@app.post("/subscription/upgrade")
async def upgrade_subscription(user_id: str, tier_code: str, user: User = Depends(get_current_user)):
    """升级订阅（模拟支付）- 升级时赠送新等级1个月配额"""
    if user_id != user.user_id:
        raise HTTPException(status_code=403, detail="无权限操作")
    if tier_code not in TIER_CONFIGS:
        raise HTTPException(status_code=400, detail="无效的订阅等级")

    tier_config = TIER_CONFIGS[tier_code]

    db = SessionLocal()
    try:
        tier = db.query(UserTier).filter(UserTier.tier_code == tier_code).first()
        if not tier:
            raise HTTPException(status_code=404, detail="订阅等级不存在")

        # 检查现有订阅
        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).first()

        # 判断是升级还是降级
        current_tier_code = None
        if existing:
            current_tier = db.query(UserTier).filter(UserTier.id == existing.tier_id).first()
            current_tier_code = current_tier.tier_code if current_tier else None

        grant_tokens = 0
        if existing:
            existing.tier_id = tier.id
            existing.updated_at = datetime.utcnow()
            # 升级：赠送新等级1个月配额
            if current_tier_code == "basic" and tier_code == "pro":
                grant_tokens = tier_config["monthly_token_quota"]  # 500万
        else:
            subscription = Subscription(
                user_id=user_id,
                tier_id=tier.id,
                status="active",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            db.add(subscription)
            # 新订阅默认基础版，没有升级不赠送

        # 升级赠送token
        token_granted = 0
        if grant_tokens > 0:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
            if not account:
                account = TokenAccount(user_id=user_id, balance=0)
                db.add(account)
            account.balance += grant_tokens
            account.total_granted += grant_tokens
            transaction = TokenTransaction(
                user_id=user_id,
                transaction_type="grant",
                amount=grant_tokens,
                balance_after=account.balance,
                description=f"升级到{tier.tier_name}赠送 {grant_tokens} Token"
            )
            db.add(transaction)
            token_granted = grant_tokens

        db.commit()

        return {
            "status": "success",
            "message": f"已升级到{tier.tier_name}",
            "data": {
                "tier": tier_code,
                "tier_name": tier.tier_name,
                "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "token_granted": token_granted
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/tiers")
async def get_available_tiers():
    """获取可用订阅等级列表"""
    db = SessionLocal()
    try:
        tiers = db.query(UserTier).filter(UserTier.is_active == True).all()
        return {
            "status": "success",
            "data": [{
                "tier_code": t.tier_code,
                "tier_name": t.tier_name,
                "description": t.description,
                "monthly_token_quota": t.monthly_token_quota,
                "token_per_message": t.token_per_message,
                "price_monthly": t.price_monthly,
                "agent_type": t.agent_type
            } for t in tiers]
        }
    finally:
        db.close()


# ==================== Admin 管理接口 ====================

def get_current_admin_user(authorization: str = Header(None)):
    """验证 Admin JWT Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="无效的认证方案")
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的认证格式")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌已过期或无效")

    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == payload.get("sub")).first()
        if not admin or not admin.is_active:
            raise HTTPException(status_code=403, detail="无权限访问")
        return admin
    finally:
        db.close()



@app.get("/admin/stats/overview")
async def admin_get_overview(admin: AdminUser = Depends(get_current_admin_user)):
    """获取管理后台概览统计"""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta

        total_users = db.query(User).count()
        total_admins = db.query(AdminUser).count()

        # Token 统计
        total_tokens = db.query(TokenAccount).all()
        total_balance = sum(a.balance for a in total_tokens)
        total_consumed = sum(a.total_consumed for a in total_tokens)
        total_purchased = sum(a.total_purchased for a in total_tokens)

        # 订阅统计
        active_subs = db.query(Subscription).filter(Subscription.status == "active").count()
        total_subs = db.query(Subscription).count()

        # 今日/本周新增用户
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        new_users_today = db.query(User).filter(User.created_at >= today_start).count()
        new_users_week = db.query(User).filter(User.created_at >= week_start).count()

        # 知识库统计
        total_knowledge_files = db.query(KnowledgeFile).count()
        indexed_files = db.query(KnowledgeFile).filter(KnowledgeFile.is_indexed == True).count()

        # Agent 分布（基于subscriptions表，UserTierRelation已弃用）
        agent_counts = {}
        for sub in db.query(Subscription).filter(Subscription.status == "active").all():
            tier_obj = db.query(UserTier).filter(UserTier.id == sub.tier_id).first()
            tier_name = tier_obj.tier_name if tier_obj else "未知"
            agent_counts[tier_name] = agent_counts.get(tier_name, 0) + 1

        # Token 账户统计
        token_accounts = db.query(TokenAccount).count()
        zero_balance_users = db.query(TokenAccount).filter(TokenAccount.balance == 0).count()

        # 知识库各 collection 向量统计
        tax_basic_stats = get_collection_stats("tax_basic")
        tax_pro_stats = get_collection_stats("tax_pro")

        return {
            "status": "success",
            "data": {
                # 用户
                "total_users": total_users,
                "total_admins": total_admins,
                "new_users_today": new_users_today,
                "new_users_week": new_users_week,
                "agent_distribution": agent_counts,
                # Token
                "total_balance": total_balance,
                "total_consumed": total_consumed,
                "total_purchased": total_purchased,
                "token_accounts": token_accounts,
                "zero_balance_users": zero_balance_users,
                # 订阅
                "active_subscriptions": active_subs,
                "total_subscriptions": total_subs,
                # 知识库
                "total_knowledge_files": total_knowledge_files,
                "indexed_files": indexed_files,
                "tax_basic_vectors": tax_basic_stats.get("vectors_count", 0),
                "tax_pro_vectors": tax_pro_stats.get("vectors_count", 0)
            }
        }
    finally:
        db.close()


@app.get("/admin/users")
async def admin_list_users(
    page: int = 1,
    page_size: int = 20,
    tier: Optional[str] = None,
    is_active: Optional[str] = None,
    search: Optional[str] = None,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取用户列表"""
    db = SessionLocal()
    try:
        query = db.query(User)

        # 搜索筛选
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.nickname.contains(search)) |
                (User.phone.contains(search))
            )

        # 状态筛选
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true' if isinstance(is_active, str) else is_active
            query = query.filter(User.is_active == is_active_bool)

        # 版本筛选 - 通过 subscriptions 表的 tier_id 关联 UserTier.id 再匹配 tier_code
        if tier:
            tier_obj = db.query(UserTier).filter(UserTier.tier_code == tier).first()
            if tier_obj:
                tier_user_ids = [sub.user_id for sub in db.query(Subscription).filter(
                    Subscription.tier_id == tier_obj.id,
                    Subscription.status == "active"
                ).all()]
                query = query.filter(User.user_id.in_(tier_user_ids))
            else:
                query = query.filter(User.user_id.in_([]))

        # 先获取所有匹配的用户（不分页，用于排序）
        all_users = query.all()
        total = len(all_users)

        # 构建用户数据并附加排序字段
        user_data_with_sort = []
        for u in all_users:
            account = db.query(TokenAccount).filter(TokenAccount.user_id == u.user_id).first()
            sub = db.query(Subscription).filter(
                Subscription.user_id == u.user_id,
                Subscription.status == "active"
            ).first()
            tier_obj = None
            if sub:
                tier_obj = db.query(UserTier).filter(UserTier.id == sub.tier_id).first()
            user_tier = db.query(UserTierRelation).filter(UserTierRelation.user_id == u.user_id).first()
            uploaded_files = db.query(KnowledgeFile).filter(KnowledgeFile.user_id == u.user_id).count()

            user_data = {
                "user_id": u.user_id,
                "username": u.username,
                "nickname": u.nickname,
                "email": u.email,
                "phone": u.phone,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "last_login_ts": u.last_login.timestamp() if u.last_login else 0,
                "created_at_ts": u.created_at.timestamp() if u.created_at else 0,
                "token_balance": account.balance if account else 0,
                "token_total_consumed": account.total_consumed if account else 0,
                "token_total_purchased": account.total_purchased if account else 0,
                "tier": tier_obj.tier_code if tier_obj else (user_tier.tier_id if user_tier else "basic"),
                "tier_name": tier_obj.tier_name if tier_obj else "基础版",
                "subscription_end": sub.end_date.isoformat() if sub and sub.end_date else None,
                "subscription_end_ts": sub.end_date.timestamp() if sub and sub.end_date else 0,
                "subscription_status": sub.status if sub else None,
                "uploaded_files": uploaded_files,
                "total_conversations": len(set([c.session_id for c in db.query(ConversationHistory).filter(ConversationHistory.user_id == u.user_id).all()])),
                "total_recharge_tokens": db.query(func.coalesce(func.sum(TokenTransaction.amount), 0)).filter(TokenTransaction.user_id == u.user_id, TokenTransaction.transaction_type == "purchase").scalar()
            }
            user_data_with_sort.append(user_data)

        # 排序
        sort_field = sort_field or "created_at"
        sort_order = sort_order or "desc"
        reverse = sort_order.lower() == "desc"

        sort_field_map = {
            "token_balance": lambda x: x["token_balance"],
            "total_recharge_tokens": lambda x: x["total_recharge_tokens"],
            "total_conversations": lambda x: x["total_conversations"],
            "subscription_end": lambda x: x["subscription_end_ts"],
            "created_at": lambda x: x["created_at_ts"],
            "last_login": lambda x: x["last_login_ts"],
        }

        if sort_field in sort_field_map:
            user_data_with_sort.sort(key=sort_field_map[sort_field], reverse=reverse)

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = user_data_with_sort[start:end]

        # 移除排序用的时间戳字段
        for u in paginated_users:
            u.pop("last_login_ts", None)
            u.pop("created_at_ts", None)
            u.pop("subscription_end_ts", None)

        return {
            "status": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "users": paginated_users
            }
        }
    finally:
        db.close()


@app.put("/admin/users/{user_id}/toggle-status")
async def admin_toggle_user_status(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """启用/禁用用户"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.is_active = not user.is_active
        db.commit()

        return {
            "status": "success",
            "message": f"用户已{'启用' if user.is_active else '禁用'}"
        }
    finally:
        db.close()


@app.post("/admin/users/{user_id}/grant-token")
async def admin_grant_token(
    user_id: str,
    amount: int,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """管理员赠送 Token"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于0")

    db = SessionLocal()
    try:
        account = db.query(TokenAccount).filter(TokenAccount.user_id == user_id).first()
        if not account:
            account = TokenAccount(user_id=user_id, balance=0)
            db.add(account)

        account.balance += amount
        account.total_granted += amount

        transaction = TokenTransaction(
            user_id=user_id,
            transaction_type="grant",
            amount=amount,
            balance_after=account.balance,
            description=f"管理员 {admin.username} 赠送"
        )
        db.add(transaction)
        db.commit()

        return {
            "status": "success",
            "message": f"已赠送 {amount} Token",
            "data": {"balance": account.balance}
        }
    finally:
        db.close()


@app.get("/admin/stats/token-usage")
async def admin_token_stats(admin: AdminUser = Depends(get_current_admin_user)):
    """Token 使用统计"""
    db = SessionLocal()
    try:
        # 总体统计
        all_accounts = db.query(TokenAccount).all()
        total_balance = sum(a.balance for a in all_accounts)
        total_consumed = sum(a.total_consumed for a in all_accounts)
        total_purchased = sum(a.total_purchased for a in all_accounts)
        zero_balance = sum(1 for a in all_accounts if a.balance == 0)

        # Token 分布（按 tier）
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

        # Top 消费者
        top_consumers = db.query(TokenAccount, User).join(
            User, TokenAccount.user_id == User.user_id
        ).order_by(TokenAccount.total_consumed.desc()).limit(20).all()

        # 最近 Token 交易
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


@app.get("/admin/stats/conversation")
async def admin_conversation_stats(admin: AdminUser = Depends(get_current_admin_user)):
    """对话统计分析"""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        # 基础统计
        total_conversations = db.query(ConversationHistory).count()
        total_users_with_chat = db.query(ConversationHistory.user_id).distinct().count()

        # 对话消息数趋势（最近30天）
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

        # Token 消耗趋势（最近30天，从 token_transactions 表）
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

        # 按 Agent 类型分布（只统计已知的 agent 类型）
        agent_stats = {}
        valid_agents = ['tax_basic', 'tax_pro']
        for agent_type in valid_agents:
            count = db.query(ConversationHistory).filter(
                ConversationHistory.agent_type == agent_type
            ).count()
            if count > 0:
                agent_stats[agent_type] = count

        # 今日/本周/本月统计
        today_messages = db.query(ConversationHistory).filter(
            ConversationHistory.created_at >= today_start
        ).count()
        week_messages = db.query(ConversationHistory).filter(
            ConversationHistory.created_at >= week_start
        ).count()
        month_messages = db.query(ConversationHistory).filter(
            ConversationHistory.created_at >= month_start
        ).count()

        # 活跃用户（7天内有对话）
        active_users_7d = db.query(ConversationHistory.user_id).filter(
            ConversationHistory.created_at >= (now - timedelta(days=7))
        ).distinct().count()

        # 沉默用户（注册但从未对话）
        all_users = db.query(User).count()
        silent_users = all_users - total_users_with_chat

        # 人均对话数
        avg_messages_per_user = round(total_conversations / total_users_with_chat, 1) if total_users_with_chat > 0 else 0

        # 平均会话长度（每 session 的消息数）
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


# ==================== Agent 配置管理接口 ====================

@app.get("/admin/agents")
async def admin_list_agents(admin: AdminUser = Depends(get_current_admin_user)):
    """获取 Agent 配置列表"""
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        return {
            "status": "success",
            "data": [{
                "id": a.id,
                "agent_type": a.agent_type,
                "name": a.name,
                "model": a.model,
                "prompt": a.prompt,
                "is_active": a.is_active
            } for a in agents]
        }
    finally:
        db.close()


@app.post("/admin/agents")
async def admin_create_agent(
    agent_type: str,
    name: str,
    prompt: str,
    model: str = "deepseek-chat",
    is_active: bool = True,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """创建 Agent 配置"""
    db = SessionLocal()
    try:
        existing = db.query(Agent).filter(Agent.agent_type == agent_type).first()
        if existing:
            raise HTTPException(status_code=400, detail="Agent 类型已存在")

        agent = Agent(agent_type=agent_type, name=name, prompt=prompt, model=model, is_active=is_active)
        db.add(agent)
        db.commit()

        return {
            "status": "success",
            "message": f"Agent {name} 创建成功",
            "data": {
                "id": agent.id,
                "agent_type": agent.agent_type,
                "name": agent.name,
                "model": agent.model,
                "is_active": agent.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.put("/admin/agents/{agent_id}")
async def admin_update_agent(
    agent_id: int,
    name: Optional[str] = None,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """更新 Agent 配置"""
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")

        if name is not None:
            agent.name = name
        if prompt is not None:
            agent.prompt = prompt
        if model is not None:
            agent.model = model
        if is_active is not None:
            agent.is_active = is_active

        db.commit()

        return {
            "status": "success",
            "message": "Agent 更新成功",
            "data": {
                "id": agent.id,
                "agent_type": agent.agent_type,
                "name": agent.name,
                "model": agent.model,
                "is_active": agent.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.delete("/admin/agents/{agent_id}")
async def admin_delete_agent(
    agent_id: int,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """删除 Agent 配置"""
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")

        db.delete(agent)
        db.commit()

        return {
            "status": "success",
            "message": "Agent 删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== 订阅版本管理接口 ====================

@app.get("/admin/tiers")
async def admin_list_tiers(admin: AdminUser = Depends(get_current_admin_user)):
    """获取订阅版本列表"""
    db = SessionLocal()
    try:
        tiers = db.query(UserTier).all()
        return {
            "status": "success",
            "data": [{
                "id": t.id,
                "tier_code": t.tier_code,
                "tier_name": t.tier_name,
                "description": t.description,
                "monthly_token_quota": t.monthly_token_quota,
                "token_per_message": t.token_per_message,
                "price_monthly": t.price_monthly,
                "agent_type": t.agent_type,
                "is_active": t.is_active
            } for t in tiers]
        }
    finally:
        db.close()


@app.post("/admin/tiers")
async def admin_create_tier(
    tier_code: str,
    tier_name: str,
    description: str,
    monthly_token_quota: int,
    token_per_message: int,
    price_monthly: int,
    agent_type: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """创建订阅版本"""
    db = SessionLocal()
    try:
        existing = db.query(UserTier).filter(UserTier.tier_code == tier_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="版本代码已存在")

        tier = UserTier(
            tier_code=tier_code,
            tier_name=tier_name,
            description=description,
            monthly_token_quota=monthly_token_quota,
            token_per_message=token_per_message,
            price_monthly=price_monthly,
            agent_type=agent_type,
            is_active=True
        )
        db.add(tier)
        db.commit()

        return {
            "status": "success",
            "message": f"订阅版本 {tier_name} 创建成功",
            "data": {
                "id": tier.id,
                "tier_code": tier.tier_code,
                "tier_name": tier.tier_name,
                "agent_type": tier.agent_type
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.put("/admin/tiers/{tier_id}")
async def admin_update_tier(
    tier_id: int,
    tier_name: Optional[str] = None,
    description: Optional[str] = None,
    monthly_token_quota: Optional[int] = None,
    token_per_message: Optional[int] = None,
    price_monthly: Optional[int] = None,
    agent_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """更新订阅版本"""
    db = SessionLocal()
    try:
        tier = db.query(UserTier).filter(UserTier.id == tier_id).first()
        if not tier:
            raise HTTPException(status_code=404, detail="订阅版本不存在")

        if tier_name is not None:
            tier.tier_name = tier_name
        if description is not None:
            tier.description = description
        if monthly_token_quota is not None:
            tier.monthly_token_quota = monthly_token_quota
        if token_per_message is not None:
            tier.token_per_message = token_per_message
        if price_monthly is not None:
            tier.price_monthly = price_monthly
        if agent_type is not None:
            tier.agent_type = agent_type
        if is_active is not None:
            tier.is_active = is_active

        db.commit()

        return {
            "status": "success",
            "message": "订阅版本更新成功",
            "data": {
                "id": tier.id,
                "tier_code": tier.tier_code,
                "tier_name": tier.tier_name,
                "agent_type": tier.agent_type,
                "is_active": tier.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.delete("/admin/tiers/{tier_id}")
async def admin_delete_tier(
    tier_id: int,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """删除订阅版本"""
    db = SessionLocal()
    try:
        tier = db.query(UserTier).filter(UserTier.id == tier_id).first()
        if not tier:
            raise HTTPException(status_code=404, detail="订阅版本不存在")

        db.delete(tier)
        db.commit()

        return {
            "status": "success",
            "message": "订阅版本删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== 系统配置接口 ====================

@app.get("/admin/system-configs")
async def admin_list_configs(admin: AdminUser = Depends(get_current_admin_user)):
    """获取系统配置"""
    db = SessionLocal()
    try:
        configs = db.query(SystemConfig).all()
        return {
            "status": "success",
            "data": {c.key: c.value for c in configs}
        }
    finally:
        db.close()


@app.put("/admin/system-configs/{key}")
async def admin_update_config(
    key: str,
    value: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """更新系统配置"""
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            config.value = value
            config.updated_by = admin.username
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(key=key, value=value, updated_by=admin.username)
            db.add(config)
        db.commit()

        return {"status": "success", "message": "配置已更新"}
    finally:
        db.close()


# ==================== 知识库管理接口 ====================

@app.get("/admin/knowledge/files")
async def admin_list_knowledge_files(
    page: int = 1,
    page_size: int = 20,
    agent_type: Optional[str] = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取所有用户的知识库文件列表（去重，同一个 doc_id 只显示一条）"""
    db = SessionLocal()
    try:
        from core.database import User
        from sqlalchemy import func

        # 子查询：按 doc_id 和 agent_type 分组，取第一条记录的字段
        subquery = db.query(
            KnowledgeFile.doc_id,
            KnowledgeFile.agent_type,
            func.max(KnowledgeFile.id).label("id"),
            func.max(KnowledgeFile.original_filename).label("original_filename"),
            func.max(KnowledgeFile.filename).label("filename"),
            func.max(KnowledgeFile.file_size).label("file_size"),
            func.max(KnowledgeFile.file_type).label("file_type"),
            func.max(KnowledgeFile.chunk_count).label("chunk_count"),
            func.max(KnowledgeFile.is_indexed).label("is_indexed"),
            func.max(KnowledgeFile.created_at).label("created_at"),
            func.count(KnowledgeFile.user_id).label("引用次数")
        )

        if agent_type:
            subquery = subquery.filter(KnowledgeFile.agent_type == agent_type)

        subquery = subquery.group_by(
            KnowledgeFile.doc_id,
            KnowledgeFile.agent_type
        ).subquery()

        # 统计去重后的总数
        total = db.query(func.count()).select_from(subquery).scalar()

        # 分页
        offset = (page - 1) * page_size
        files = db.query(subquery).order_by(subquery.c.created_at.desc()).offset(offset).limit(page_size).all()

        # 获取上传者信息（取 doc_id 对应的 admin 用户）
        # 如果有 admin 上传的文件，user_id 为 admin；否则取第一个保存引用的用户
        result_files = []
        for f in files:
            # 查找这个 doc_id 的原始上传者
            original = db.query(KnowledgeFile).filter(
                KnowledgeFile.doc_id == f.doc_id,
                KnowledgeFile.agent_type == f.agent_type,
                KnowledgeFile.user_id == 'admin'
            ).first()

            if original:
                uploader = "平台"
                user_id = "admin"
            else:
                first_user = db.query(KnowledgeFile).filter(
                    KnowledgeFile.doc_id == f.doc_id,
                    KnowledgeFile.agent_type == f.agent_type
                ).first()
                uploader = first_user.user_id if first_user else "未知"
                user_id = first_user.user_id if first_user else "未知"

            result_files.append({
                "id": f.id,
                "user_id": user_id,
                "username": uploader,
                "filename": f.filename,
                "original_filename": f.original_filename,
                "file_size": f.file_size,
                "file_type": f.file_type,
                "agent_type": f.agent_type,
                "doc_id": f.doc_id,
                "chunk_count": f.chunk_count,
                "is_indexed": f.is_indexed,
                "引用次数": f.引用次数,
                "created_at": f.created_at.isoformat() if f.created_at else None
            })

        return {
            "status": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "files": result_files
            }
        }
    finally:
        db.close()


@app.post("/admin/knowledge/files")
async def admin_upload_knowledge_file(
    agent_type: str = "tax_basic",
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin_user)
):
    """admin 上传 PDF 文件到知识库"""
    # 检查文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()

    file_size = file_path.stat().st_size

    # 记录到数据库（admin 上传 user_id 为 "admin"）
    db = SessionLocal()
    try:
        # 检查同名文件是否已有记录，有则清理旧向量避免重复
        existing = db.query(KnowledgeFile).filter(
            KnowledgeFile.user_id == "admin",
            KnowledgeFile.original_filename == file.filename
        ).first()
        if existing and existing.doc_id:
            delete_from_vectorstore(existing.doc_id, agent_type)

        kf = KnowledgeFile(
            user_id="admin",
            filename=safe_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type="pdf",
            agent_type=agent_type,
            is_indexed=False
        )
        db.add(kf)
        db.commit()
        db.refresh(kf)
    finally:
        db.close()

    # 处理文件并索引到向量库
    try:
        result = upload_and_index_pdf(str(file_path), agent_type)

        # 更新索引状态和doc_id
        db = SessionLocal()
        try:
            kf = db.query(KnowledgeFile).filter(KnowledgeFile.filename == safe_filename).first()
            if kf:
                kf.is_indexed = True
                kf.doc_id = result.get("doc_id")
                kf.chunk_count = result.get("chunks", 0)
                db.commit()
        finally:
            db.close()

        return {
            "status": "success",
            "message": "文件上传并索引成功",
            "data": {
                "id": kf.id if kf else None,
                "filename": safe_filename,
                "doc_id": result.get("doc_id"),
                "chunks": result.get("chunks", 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@app.delete("/admin/knowledge/files/{filename}")
async def admin_delete_knowledge_file(
    filename: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """从知识库删除文件（从数据库和向量库都删除）"""
    db = SessionLocal()
    try:
        kf = db.query(KnowledgeFile).filter(KnowledgeFile.filename == filename).first()
        if not kf:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 删除物理文件
        file_path = Path(kf.file_path)
        if file_path.exists():
            file_path.unlink()

        # 从向量库删除
        if kf.doc_id and kf.agent_type:
            try:
                delete_from_vectorstore(kf.agent_type, kf.doc_id)
            except Exception as e:
                print(f"向量库删除失败: {e}")

        db.delete(kf)
        db.commit()

        return {"status": "success", "message": "文件已删除"}
    finally:
        db.close()


@app.get("/admin/knowledge/stats")
async def admin_knowledge_stats(admin: AdminUser = Depends(get_current_admin_user)):
    """获取知识库统计信息"""
    db = SessionLocal()
    try:
        total_files = db.query(KnowledgeFile).count()
        indexed_files = db.query(KnowledgeFile).filter(KnowledgeFile.is_indexed == True).count()
        total_size = db.query(KnowledgeFile).with_entities(func.sum(KnowledgeFile.file_size)).scalar() or 0

        # 获取各 collection 的向量统计
        tax_basic_stats = get_collection_stats("tax_basic")
        tax_pro_stats = get_collection_stats("tax_pro")

        return {
            "status": "success",
            "data": {
                "total_files": total_files,
                "indexed_files": indexed_files,
                "total_size_bytes": total_size,
                "collections": {
                    "tax_basic": tax_basic_stats,
                    "tax_pro": tax_pro_stats
                }
            }
        }
    finally:
        db.close()


@app.get("/admin/knowledge/files/{filename}/chunks")
async def admin_get_file_chunks(
    filename: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取指定文件的 chunks 列表"""
    db = SessionLocal()
    try:
        kf = db.query(KnowledgeFile).filter(KnowledgeFile.filename == filename).first()
        if not kf:
            raise HTTPException(status_code=404, detail="文件不存在")

        if not kf.doc_id or not kf.agent_type:
            return {"status": "success", "chunks": [], "total": 0, "message": "文件未索引"}

        result = get_file_chunks(kf.agent_type, kf.doc_id)
        return result
    finally:
        db.close()


@app.get("/admin/knowledge/search")
async def admin_knowledge_search(
    query: str,
    agent_type: str = "tax_basic",
    top_k: int = 5,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """RAG 检索测试"""
    result = search_knowledge_preview(query, agent_type, top_k)
    return result


@app.get("/admin/knowledge/export")
async def admin_export_knowledge(
    agent_type: str = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """导出知识库文件列表"""
    db = SessionLocal()
    try:
        query = db.query(KnowledgeFile)
        if agent_type:
            query = query.filter(KnowledgeFile.agent_type == agent_type)
        files = query.order_by(KnowledgeFile.created_at.desc()).all()

        export_data = []
        for f in files:
            export_data.append({
                "original_filename": f.original_filename,
                "filename": f.filename,
                "agent_type": f.agent_type,
                "file_size": f.file_size,
                "chunk_count": f.chunk_count,
                "is_indexed": f.is_indexed,
                "doc_id": f.doc_id,
                "created_at": f.created_at.isoformat() if f.created_at else None
            })

        return {
            "status": "success",
            "data": {
                "export_time": datetime.utcnow().isoformat(),
                "total_files": len(export_data),
                "files": export_data
            }
        }
    finally:
        db.close()


@app.post("/admin/knowledge/import")
async def admin_import_knowledge(
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin_user)
):
    """导入知识库文件列表（JSON格式）"""
    db = SessionLocal()
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))

        if "files" not in data:
            raise HTTPException(status_code=400, detail="无效的导入文件格式")

        imported_count = 0
        for item in data["files"]:
            # 检查是否已存在
            existing = db.query(KnowledgeFile).filter(
                KnowledgeFile.filename == item.get("filename")
            ).first()

            if existing:
                # 更新现有记录
                existing.original_filename = item.get("original_filename", existing.original_filename)
                existing.agent_type = item.get("agent_type", existing.agent_type)
                existing.chunk_count = item.get("chunk_count", existing.chunk_count)
                existing.is_indexed = item.get("is_indexed", existing.is_indexed)
                existing.doc_id = item.get("doc_id", existing.doc_id)
            else:
                # 创建新记录（不复制文件）
                kf = KnowledgeFile(
                    user_id="admin",
                    username="admin",
                    filename=item.get("filename"),
                    original_filename=item.get("original_filename", item.get("filename")),
                    file_path="",
                    file_size=item.get("file_size", 0),
                    agent_type=item.get("agent_type"),
                    doc_id=item.get("doc_id"),
                    chunk_count=item.get("chunk_count", 0),
                    is_indexed=item.get("is_indexed", False)
                )
                db.add(kf)

            imported_count += 1

        db.commit()
        return {
            "status": "success",
            "message": f"成功导入 {imported_count} 条记录"
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    from tasks.scheduler import start_scheduler
    start_scheduler()
    uvicorn.run(app, host="0.0.0.0", port=8000)