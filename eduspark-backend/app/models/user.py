"""用户表"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # relationships
    profile: Mapped[StudentProfile] = relationship(back_populates="user", uselist=False)
    chat_histories: Mapped[list[ChatHistory]] = relationship(back_populates="user")
    evaluation_reports: Mapped[list[EvaluationReport]] = relationship(back_populates="user")
