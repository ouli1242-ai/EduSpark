"""知识图谱数据模型"""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class KnowledgeGraphNode(Base):
    """知识图谱节点表"""
    __tablename__ = "knowledge_graph"

    id: Mapped[int] = mapped_column(primary_key=True)
    course: Mapped[str] = mapped_column(String(100), index=True)  # "机器学习"
    name: Mapped[str] = mapped_column(String(200))  # "线性回归"
    chapter: Mapped[int] = mapped_column(Integer, default=0)  # 教材章节号
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1-5

    # 依赖关系（存储为 ID 列表）
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)  # 前置知识 ID
    related: Mapped[list] = mapped_column(JSON, default=list)  # 相关知识 ID

    # 描述
    description: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
