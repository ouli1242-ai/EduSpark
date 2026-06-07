"""学习行为记录表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 行为类型：view(查看资源) | complete(完成学习) | quiz(做题) | chat(对话)
    action: Mapped[str] = mapped_column(String(50))
    # 关联资源 ID（可选）
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), nullable=True)
    # 关联知识点
    knowledge_point: Mapped[str] = mapped_column(String(200), default="")

    # 行为详情（JSON）
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    # quiz: {"score": 85, "total": 100, "correct": 17, "wrong": 3}
    # view: {"duration_seconds": 300}
    # complete: {"topic": "线性回归"}

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
