"""Conversation persistence for the assistant."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = mapped_column(String(48), primary_key=True)
    user_id = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = mapped_column(String(120), nullable=False, server_default="Conversation")
    created_at = mapped_column(String(40), nullable=False)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation", order_by="ConversationMessage.created_at"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = mapped_column(String(48), primary_key=True)
    conversation_id = mapped_column(String(48), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = mapped_column(String(16), nullable=False)  # user | assistant
    text = mapped_column(Text, nullable=False)
    response_json = mapped_column(Text, nullable=True)
    created_at = mapped_column(String(40), nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    __table_args__ = (Index("ix_convmsg_conversation", "conversation_id"),)


class AssistantExecution(Base):
    __tablename__ = "assistant_executions"

    id = mapped_column(String(48), primary_key=True)
    conversation_id = mapped_column(String(48), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    message_id = mapped_column(String(48), ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=False)
    intent = mapped_column(String(60), nullable=False)
    tool = mapped_column(String(60), nullable=True)
    status = mapped_column(String(20), nullable=False, server_default="ok")
    detail = mapped_column(Text, nullable=True)
    created_at = mapped_column(String(40), nullable=False)
