"""对话历史表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 会话 ID（同一轮对话共享）
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    # 消息角色：user | assistant | system
    role: Mapped[str] = mapped_column(String(20))
    # 消息内容
    content: Mapped[str] = mapped_column(Text)
    # Agent 类型（assistant 消息时）：profile | resource | path | tutor | evaluation
    agent_type: Mapped[str] = mapped_column(String(30), nullable=True)
    # 额外元数据（如资源生成结果、Agent 状态等）
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # relationships
    user: Mapped["User"] = relationship(back_populates="chat_histories")  # noqa: F821
