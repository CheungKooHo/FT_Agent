# -*- coding: utf-8 -*-
import shutil
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
from datetime import datetime
from sqlalchemy import func

from core.database import SessionLocal, AdminUser, KnowledgeFile
from core.rag_engine import (
    upload_and_index_pdf, search_knowledge_preview, get_collection_stats,
    get_file_chunks, delete_from_vectorstore
)
from routes.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin知识库"])

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/knowledge/files")
async def admin_list_knowledge_files(
    page: int = 1,
    page_size: int = 20,
    agent_type: Optional[str] = None,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """获取所有用户的知识库文件列表"""
    db = SessionLocal()
    try:
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

        total = db.query(func.count()).select_from(subquery).scalar()

        offset = (page - 1) * page_size
        files = db.query(subquery).order_by(subquery.c.created_at.desc()).offset(offset).limit(page_size).all()

        result_files = []
        for f in files:
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


@router.post("/knowledge/files")
async def admin_upload_knowledge_file(
    agent_type: str = "tax_basic",
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin_user)
):
    """admin 上传 PDF 文件到知识库"""
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


@router.delete("/knowledge/files/{filename}")
async def admin_delete_knowledge_file(
    filename: str,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """从知识库删除文件"""
    db = SessionLocal()
    try:
        kf = db.query(KnowledgeFile).filter(KnowledgeFile.filename == filename).first()
        if not kf:
            raise HTTPException(status_code=404, detail="文件不存在")

        file_path = Path(kf.file_path)
        if file_path.exists():
            file_path.unlink()

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


@router.get("/knowledge/stats")
async def admin_knowledge_stats(admin: AdminUser = Depends(get_current_admin_user)):
    """获取知识库统计信息"""
    db = SessionLocal()
    try:
        total_files = db.query(KnowledgeFile).count()
        indexed_files = db.query(KnowledgeFile).filter(KnowledgeFile.is_indexed == True).count()
        total_size = db.query(KnowledgeFile).with_entities(func.sum(KnowledgeFile.file_size)).scalar() or 0

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


@router.get("/knowledge/files/{filename}/chunks")
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


@router.get("/knowledge/search")
async def admin_knowledge_search(
    query: str,
    agent_type: str = "tax_basic",
    top_k: int = 5,
    admin: AdminUser = Depends(get_current_admin_user)
):
    """RAG 检索测试"""
    result = search_knowledge_preview(query, agent_type, top_k)
    return result


@router.get("/knowledge/export")
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


@router.post("/knowledge/import")
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
            existing = db.query(KnowledgeFile).filter(
                KnowledgeFile.filename == item.get("filename")
            ).first()

            if existing:
                existing.original_filename = item.get("original_filename", existing.original_filename)
                existing.agent_type = item.get("agent_type", existing.agent_type)
                existing.chunk_count = item.get("chunk_count", existing.chunk_count)
                existing.is_indexed = item.get("is_indexed", existing.is_indexed)
                existing.doc_id = item.get("doc_id", existing.doc_id)
            else:
                kf = KnowledgeFile(
                    user_id="admin",
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
