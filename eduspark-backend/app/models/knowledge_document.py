"""知识文档表 — 上传的教材/课件/习题等"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 原始文件名
    original_name: Mapped[str] = mapped_column(String(200))
    # 文件类型：pdf / ppt / docx / txt
    file_type: Mapped[str] = mapped_column(String(20))
    # 文件大小（字节）
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    # 存储路径
    storage_path: Mapped[str] = mapped_column(String(500))

    # 解析状态：pending / parsing / completed / failed
    parse_status: Mapped[str] = mapped_column(String(20), default="pending")
    # 解析后的纯文本（摘要，前5000字）
    parsed_text: Mapped[str] = mapped_column(Text, default="")
    # 解析详情
    parse_detail: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"pages": 30, "char_count": 50000, "chunks_count": 80}

    # 关联课程/知识点
    course: Mapped[str] = mapped_column(String(100), default="")
    knowledge_points: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
