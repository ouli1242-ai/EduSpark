"""学习资源表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum


class ResourceType(str, enum.Enum):
    DOCUMENT = "document"       # 课程讲解文档
    QUIZ = "quiz"               # 练习题目
    MINDMAP = "mindmap"         # 思维导图
    CODE = "code"               # 代码案例
    VIDEO = "video"             # 教学视频
    READING = "reading"         # 拓展阅读


class ResourceStatus(str, enum.Enum):
    GENERATING = "generating"   # 生成中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 生成失败


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[ResourceType] = mapped_column(SQLEnum(ResourceType))
    status: Mapped[ResourceStatus] = mapped_column(SQLEnum(ResourceStatus), default=ResourceStatus.GENERATING)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")          # 文本内容（Markdown/JSON）
    storage_key: Mapped[str] = mapped_column(String(500), default="")  # 文件存储路径

    # 关联知识点
    knowledge_points: Mapped[list] = mapped_column(JSON, default=list)
    # 难度级别 1-5
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    # RAG 置信度
    confidence: Mapped[str] = mapped_column(String(20), default="medium")

    # 生成参数快照（用于重新生成）
    generation_params: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
