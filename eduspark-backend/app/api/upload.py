"""文件上传接口 — 上传教材/课件/习题并自动解析"""
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.config import get_settings
from app.models.user import User
from app.models.knowledge_document import KnowledgeDocument
from app.utils.auth import get_current_user
from app.services.document_parser import doc_parser

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

settings = get_settings()


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    course: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传教材/课件/习题文件，自动解析文本内容"""
    # 1. 校验文件类型
    filename = file.filename or "unknown"
    suffix = Path(filename).suffix.lower()
    allowed_types = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".txt", ".md"}
    if suffix not in allowed_types:
        raise HTTPException(400, f"不支持的文件格式: {suffix}，支持: {', '.join(allowed_types)}")

    # 2. 校验文件大小（最大 50MB）
    content = await file.read()
    file_size = len(content)
    max_size = 50 * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(400, f"文件过大（{file_size / 1024 / 1024:.1f}MB），最大 50MB")

    # 3. 保存到本地存储
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / "uploads"
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid.uuid4().hex[:12]
    save_name = f"{file_id}_{filename}"
    save_path = storage_dir / save_name
    save_path.write_bytes(content)

    # 4. 创建数据库记录
    doc = KnowledgeDocument(
        user_id=user.id,
        original_name=filename,
        file_type=suffix.replace(".", ""),
        file_size=file_size,
        storage_path=str(save_path),
        parse_status="pending",
        course=course,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 5. 异步解析文本
    try:
        result = doc_parser.parse(str(save_path))
        if result["success"]:
            # 分块
            chunks = doc_parser.chunk_text(result["text"])
            doc.parse_status = "completed"
            doc.parsed_text = result["text"][:10000]  # 保存前10000字预览
            doc.parse_detail = {
                "pages": result.get("pages", 0),
                "char_count": len(result["text"]),
                "chunks_count": len(chunks),
            }
        else:
            doc.parse_status = "failed"
            doc.parse_detail = {"error": result.get("error", "解析失败")}
    except Exception as e:
        doc.parse_status = "failed"
        doc.parse_detail = {"error": str(e)}

    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "original_name": doc.original_name,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "parse_status": doc.parse_status,
        "course": doc.course,
        "parse_detail": doc.parse_detail,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("")
def list_documents(
    course: str = Query(default="", description="按课程筛选"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取已上传的文档列表"""
    query = db.query(KnowledgeDocument).filter(KnowledgeDocument.user_id == user.id)
    if course:
        query = query.filter(KnowledgeDocument.course == course)
    docs = query.order_by(KnowledgeDocument.created_at.desc()).limit(50).all()

    return [
        {
            "id": d.id,
            "original_name": d.original_name,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "parse_status": d.parse_status,
            "course": d.course,
            "parse_detail": d.parse_detail,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/{doc_id}")
def get_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取文档详情（含解析后的文本内容和分块）"""
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.user_id == user.id,
    ).first()
    if not doc:
        raise HTTPException(404, "文档不存在")

    # 重新分块（从完整文本）
    chunks = doc_parser.chunk_text(doc.parsed_text) if doc.parsed_text else []

    return {
        "id": doc.id,
        "original_name": doc.original_name,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "parse_status": doc.parse_status,
        "course": doc.course,
        "knowledge_points": doc.knowledge_points,
        "parse_detail": doc.parse_detail,
        "parsed_text_preview": doc.parsed_text[:3000] if doc.parsed_text else "",
        "chunks": [
            {"index": c["index"], "char_count": c["char_count"], "preview": c["content"][:200]}
            for c in chunks
        ],
        "chunks_count": len(chunks),
        "created_at": doc.created_at.isoformat(),
    }


@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除文档（同时删除文件）"""
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.user_id == user.id,
    ).first()
    if not doc:
        raise HTTPException(404, "文档不存在")

    # 删除本地文件
    try:
        os.remove(doc.storage_path)
    except OSError:
        pass

    db.delete(doc)
    db.commit()
    return {"message": "删除成功"}
