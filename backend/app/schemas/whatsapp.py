"""Schemas Pydantic para agentes_whatsapp y documentos_generados."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AgenteWhatsappOut(BaseModel):
    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    cliente_id: Optional[UUID] = None
    lista_precios_id: Optional[UUID] = None
    tipo: str
    icono: Optional[str] = None
    color_hex: Optional[str] = None
    activo: bool
    proximo_folio: int
    requires_pesos: bool
    config: dict
    system_prompt_addendum: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentoGeneradoOut(BaseModel):
    id: UUID
    tenant_id: UUID
    agente_id: Optional[UUID] = None
    remision_id: Optional[UUID] = None
    pedido_id: Optional[UUID] = None
    tipo_documento: str
    nombre_archivo: str
    fecha_documento: Optional[date] = None
    url_storage: Optional[str] = None
    sha256: Optional[str] = None
    bytes: Optional[int] = None
    metadata_doc: dict
    created_at: datetime

    model_config = {"from_attributes": True}
