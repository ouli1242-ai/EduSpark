"""学生画像表 — 6维度"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    # 6维度画像数据（JSON 存储，灵活扩展）
    knowledge_base: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"mastered": [...], "weak": [...], "blind_spots": [...], "score": 0.0-1.0}

    cognitive_style: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"visual": 0.0-1.0, "auditory": 0.0-1.0, "kinesthetic": 0.0-1.0, "summary": "..."}

    learning_ability: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"absorption_speed": 0.0-1.0, "understanding_depth": 0.0-1.0, "transfer_ability": 0.0-1.0}

    error_patterns: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"types": [...], "root_causes": [...], "score": 0.0-1.0}

    learning_goals: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"short_term": "...", "long_term": "...", "career": "..."}

    learning_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    # {"resource_types": [...], "time_pref": "...", "difficulty_pref": "..."}

    # 对话轮次计数（用于判断画像成熟度）
    conversation_turns: Mapped[int] = mapped_column(Integer, default=0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    user: Mapped["User"] = relationship(back_populates="profile")  # noqa: F821
