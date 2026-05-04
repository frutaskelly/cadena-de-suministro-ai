"""Chat estilo ChatGPT — conversaciones persistentes con AI (Sprint 10).

Reemplaza el flujo legacy v1 (WhatsApp webhook -> Claude) por una UI web
donde el operador puede:
- Crear conversaciones nuevas con un agente especifico
- Subir archivos (Excel BD, fotos libreta, PDFs)
- Recibir respuestas de Claude
- Volver a conversaciones anteriores
"""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer, DateTime,
    Text, Index, Numeric,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin


class ChatConversacion(Base, TimestampMixin):
    """Una conversacion entre un operador y un agente AI."""
    __tablename__ = "chat_conversaciones"
    __table_args__ = (
        Index("ix_chat_conv_tenant", "tenant_id"),
        Index("ix_chat_conv_agente", "agente_id"),
        Index("ix_chat_conv_user", "user_id"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    agente_id = Column(UUID(as_uuid=True), ForeignKey("agentes_whatsapp.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    titulo = Column(String(254), nullable=False, default="Nueva conversacion")
    archivada = Column(Boolean, default=False, nullable=False, server_default="false")

    # ultima actividad para ordenar la sidebar
    ultima_actividad = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # contadores y metadata
    mensajes_count = Column(Integer, default=0, nullable=False, server_default="0")
    tokens_in = Column(Integer, default=0, nullable=False, server_default="0")
    tokens_out = Column(Integer, default=0, nullable=False, server_default="0")
    costo_usd = Column(Numeric(10, 4), default=0, nullable=False, server_default="0")

    metadata_conv = Column("metadata", JSONB, default=dict, nullable=False, server_default="{}")

    mensajes = relationship(
        "ChatMensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="ChatMensaje.created_at",
    )


class ChatMensaje(Base):
    """Mensajes de una conversacion (user / assistant / system)."""
    __tablename__ = "chat_mensajes"
    __table_args__ = (
        Index("ix_chat_msg_conversacion", "conversacion_id"),
        Index("ix_chat_msg_role", "role"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    conversacion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_conversaciones.id", ondelete="CASCADE"),
        nullable=False,
    )

    role = Column(String(15), nullable=False)  # "user", "assistant", "system"
    contenido = Column(Text, nullable=False)

    # adjuntos (lista de {tipo, nombre, mime, size, data_b64 o url_storage})
    adjuntos = Column(JSONB, default=list, nullable=False, server_default="[]")

    # metadata Claude (model, stop_reason, tokens, latencia)
    ai_metadata = Column(JSONB, default=dict, nullable=False, server_default="{}")

    # accion estructurada que el AI quiso ejecutar (procesar_archivo, registrar_pesos, etc.)
    # null = solo respuesta conversacional
    accion = Column(String(40), nullable=True)
    accion_payload = Column(JSONB, nullable=True)
    accion_resultado = Column(JSONB, nullable=True)  # output de la accion ejecutada

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversacion = relationship("ChatConversacion", back_populates="mensajes")
