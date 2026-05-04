"""Schemas Pydantic del modulo Chat."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatAttachmentIn(BaseModel):
    nombre: str
    mime: str
    size: int
    # base64 sin prefijo data: — opcional para archivos texto que se inline
    data_b64: Optional[str] = None


class ChatMensajeOut(BaseModel):
    id: UUID
    conversacion_id: UUID
    role: str
    contenido: str
    adjuntos: list[dict] = Field(default_factory=list)
    ai_metadata: dict = Field(default_factory=dict)
    accion: Optional[str] = None
    accion_payload: Optional[dict] = None
    accion_resultado: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatConversacionCreate(BaseModel):
    agente_id: Optional[UUID] = None
    titulo: Optional[str] = None


class ChatConversacionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    agente_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    titulo: str
    archivada: bool
    ultima_actividad: datetime
    mensajes_count: int
    tokens_in: int
    tokens_out: int
    metadata_conv: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatConversacionDetail(ChatConversacionOut):
    mensajes: list[ChatMensajeOut] = Field(default_factory=list)


class ChatMensajeIn(BaseModel):
    contenido: str = ""
    adjuntos: list[ChatAttachmentIn] = Field(default_factory=list)
