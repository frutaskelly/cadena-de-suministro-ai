from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ContratoBase(BaseModel):
    numero_contrato: Optional[str] = None
    contratante: str
    contratante_rfc: Optional[str] = None
    estado_mx: Optional[str] = None
    vigencia_desde: date
    vigencia_hasta: date
    monto_max: Optional[Decimal] = None
    condiciones_pago: Optional[str] = None
    notas: Optional[str] = None
    config: dict = {}


class ContratoCreate(ContratoBase):
    pass


class ContratoOut(ContratoBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ContratoLoteBase(BaseModel):
    numero_lote: int
    descripcion: str
    asignado_a_tenant: Optional[UUID] = None
    lista_precios_id: Optional[UUID] = None
    monto_lote: Optional[Decimal] = None


class ContratoLoteCreate(ContratoLoteBase):
    contrato_id: UUID


class ContratoLoteOut(ContratoLoteBase):
    id: UUID
    contrato_id: UUID

    model_config = {"from_attributes": True}


class UnidadEntregaBase(BaseModel):
    codigo: Optional[str] = None
    nombre: str
    tipo: Literal["HOSPITAL", "COMEDOR", "ESCUELA", "MILITAR", "RECLUSORIO", "ALMACEN", "OTRO"]
    ciudad: Optional[str] = None
    estado_mx: Optional[str] = None
    direccion: Optional[str] = None
    cp: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_telefono: Optional[str] = None
    contacto_email: Optional[str] = None
    geo_lat: Optional[Decimal] = None
    geo_lon: Optional[Decimal] = None
    frecuencia_entrega: Optional[str] = None
    hora_corte_pedido: Optional[time] = None
    hora_entrega: Optional[time] = None
    protocolo: dict = {}
    activa: bool = True
    notas: Optional[str] = None


class UnidadEntregaCreate(UnidadEntregaBase):
    contrato_id: UUID


class UnidadEntregaOut(UnidadEntregaBase):
    id: UUID
    contrato_id: UUID

    model_config = {"from_attributes": True}
