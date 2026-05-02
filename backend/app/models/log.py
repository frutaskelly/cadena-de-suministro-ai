"""Audit log y mensajes."""
from sqlalchemy import (
    Column, String, ForeignKey, BigInteger, DateTime, Text, Enum
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, tenant_fk


class EventLog(Base):
    __tablename__ = "events_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), index=True)
    before_state = Column(JSONB)
    after_state = Column(JSONB)
    metadata_ = Column("metadata", JSONB)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)


class MensajeLog(Base):
    __tablename__ = "mensajes_log"

    id = uuid_pk()
    tenant_id = tenant_fk()
    canal = Column(
        Enum("WHATSAPP", "EMAIL", "WEB", "SMS", "API", name="mensaje_canal"),
        nullable=False,
    )
    direccion = Column(
        Enum("IN", "OUT", name="mensaje_direccion"),
        nullable=False,
    )
    contraparte = Column(String(254), index=True)
    contenido = Column(Text)
    attachments = Column(JSONB, default=list)
    agente_id = Column(UUID(as_uuid=True))
    metadata_ = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
