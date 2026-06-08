"""评估报告数据模型"""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class EvaluationReport(Base):
    """学习效果评估报告表"""
    __tablename__ = "evaluation_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)

    # 聚合数据（JSON）
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"knowledge_mastered": 12, "knowledge_weak": [...],
    #  "learning_hours": 8.5, "resources_completed": 15, "test_accuracy": 0.82}

    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)
    # [{"action": "复习", "topic": "...", "reason": "...", "suggested_resources": [1,3]}]

    # LLM 生成的自然语言报告
    report_text: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="evaluation_reports")
