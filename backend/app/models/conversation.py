from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    # 患者是匿名用户，用 session_id 区分不同患者
    session_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="前端生成的唯一会话标识"
    )
    dify_conversation_id: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="Dify 返回的对话ID，用于多轮对话"
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation"
    )

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="user 或 assistant"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
