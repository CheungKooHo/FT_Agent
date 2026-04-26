# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from core.database import SessionLocal, User, KnowledgeFile
from core.rag_engine import (
    upload_and_index_pdf, search_knowledge_preview, get_collection_stats,
    get_file_chunks, delete_from_vectorstore
)
from routes.dependencies import get_current_user

router = APIRouter(prefix="", tags=["知识库"])

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload_file")
async def upload_file(
    agent_type: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """上传 PDF 文件到知识库"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()

    file_size = file_path.stat().st_size

    db = SessionLocal()
    try:
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

    try:
        result = upload_and_index_pdf(str(file_path), agent_type)

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


@router.get("/knowledge/files")
async def list_knowledge_files(user: User = Depends(get_current_user)):
    """获取知识库文件列表"""
    db = SessionLocal()
    try:
        files = db.query(KnowledgeFile).filter(
            KnowledgeFile.user_id == user.user_id
        ).order_by(KnowledgeFile.created_at.desc()).all()

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


@router.delete("/knowledge/files/{filename}")
async def delete_knowledge_file(
    filename: str,
    user: User = Depends(get_current_user)
):
    """删除知识库文件"""
    db = SessionLocal()
    try:
        kf = db.query(KnowledgeFile).filter(
            KnowledgeFile.filename == filename,
            KnowledgeFile.user_id == user.user_id
        ).first()

        if not kf:
            raise HTTPException(status_code=404, detail="文件不存在")

        try:
            if kf.file_path and os.path.exists(kf.file_path):
                os.remove(kf.file_path)
        except Exception:
            pass

        if kf.user_id == "admin" and kf.agent_type and kf.doc_id:
            try:
                delete_from_vectorstore(kf.agent_type, kf.doc_id)
            except Exception as e:
                print(f"向量库删除失败: {e}")

        db.delete(kf)
        db.commit()

        return {"status": "success", "message": "文件已删除"}
    finally:
        db.close()


@router.get("/knowledge/files/{filename}/chunks")
async def get_knowledge_file_chunks(
    filename: str,
    user: User = Depends(get_current_user)
):
    """获取指定知识库文件的切片列表"""
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


@router.post("/knowledge/save-reference")
async def save_reference_document(
    doc_id: str,
    source: str,
    agent_type: str = "tax_basic",
    user: User = Depends(get_current_user)
):
    """将对话中引用的文档保存到用户知识库"""
    db = SessionLocal()
    try:
        source_file = db.query(KnowledgeFile).filter(
            KnowledgeFile.doc_id == doc_id,
            KnowledgeFile.agent_type == agent_type
        ).first()

        if not source_file:
            raise HTTPException(status_code=404, detail="引用的文档不存在")

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

        kf = KnowledgeFile(
            user_id=user.user_id,
            filename=source_file.filename,
            original_filename=source_file.original_filename,
            file_path=None,
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
            "filename": source_file.original_filename,
            "doc_id": doc_id,
            "chunks": source_file.chunk_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")
    finally:
        db.close()


@router.get("/knowledge/search_preview")
async def preview_knowledge_search(
    query: str,
    agent_type: str = "tax_basic",
    top_k: int = 5,
    user: User = Depends(get_current_user)
):
    """预览知识库搜索结果"""
    result = search_knowledge_preview(query, agent_type, top_k)
    return result


@router.get("/knowledge/stats")
async def get_knowledge_stats(
    agent_type: str = "tax_basic",
    user: User = Depends(get_current_user)
):
    """获取知识库统计信息"""
    stats = get_collection_stats(agent_type)
    return stats
