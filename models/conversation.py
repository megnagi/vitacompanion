from sqlalchemy import Column, String, Boolean, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
import uuid
from db import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bot_type = Column(ENUM('orchestrator', 'nutrition', 'training', 'reporting', 'scheduler', name='bot_type', create_type=False), nullable=False, default='orchestrator')
    started_at = Column(DateTime(timezone=True), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(ENUM('user', 'assistant', 'system', name='message_role', create_type=False), nullable=False)
    bot_source = Column(ENUM('orchestrator', 'nutrition', 'training', 'reporting', 'scheduler', name='bot_type', create_type=False), nullable=True)
    content = Column(Text, nullable=False)
    raw_bot_response = Column(JSONB, nullable=True)
    persona_applied = Column(ENUM('friend', 'coach', 'commander', name='persona_style', create_type=False), nullable=True)
    safety_flag_raised = Column(Boolean, nullable=False, default=False)
    flag_type = Column(ENUM('none', 'physical', 'emotional', 'constraint_violation', 'rapid_weight_loss', 'pain_reported', 'hr_exceeded', 'overtraining_risk', 'medical_hold', name='flag_type', create_type=False), nullable=True)
    token_count = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")