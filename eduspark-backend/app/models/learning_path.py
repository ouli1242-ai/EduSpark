"""学习路径表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 路径名称（如 "机器学习入门路径"）
    name: Mapped[str] = mapped_column(String(200))
    # 目标课程
    course: Mapped[str] = mapped_column(String(100), default="机器学习")

    # 路径步骤（有序列表）
    steps: Mapped[list] = mapped_column(JSON, default=list)
    # [
    #   {
    #     "order": 1,
    #     "topic": "线性回归",
    #     "knowledge_points": ["最小二乘法", "梯度下降"],
    #     "resource_ids": [1, 2, 3],
    #     "status": "pending|current|completed",
    #     "estimated_time": "2h",
    #     "actual_time": null
    #   }
    # ]

    # 总体进度 0.0 ~ 1.0
    progress: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
