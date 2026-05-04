"""Schemas para ordenes de compra y sus lineas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class LineaOrdenCompraCreate(BaseModel):
    producto_id: UUID
    cantidad_solicitada: Decimal
    presentacion: Optional[str] = None
    precio_unitario: Decimal
    importe: Decimal
    notas: Optional[str] = None


class LineaOrdenCompraOut(LineaOrdenCompraCreate):
    id: UUID
    orden_compra_id: UUID
    cantidad_recibida: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrdenCompraCreate(BaseModel):
    folio: Optional[str] = None
    proveedor_id: UUID
    pedido_origen_id: Optional[UUID] = None
    almacen_destino_id: Optional[UUID] = None
    fecha: date
    fecha_entrega_esperada: Optional[date] = None
    estado: Literal[
        "BORRADOR", "ENVIADA", "ACEPTADA", "EN_TRANSITO",
        "RECIBIDA_PARCIAL", "RECIBIDA", "CANCELADA",
    ] = "BORRADOR"
    notas: Optional[str] = None
    lineas: list[LineaOrdenCompraCreate] = []


class OrdenCompraOut(BaseModel):
    id: UUID
    tenant_id: UUID
    folio: Optional[str]
    proveedor_id: UUID
    pedido_origen_id: Optional[UUID] = None
    almacen_destino_id: Optional[UUID] = None
    fecha: date
    fecha_entrega_esperada: Optional[date] = None
    fecha_recibida: Optional[date] = None
    estado: str
    subtotal: Optional[Decimal] = None
    iva_total: Optional[Decimal] = None
    total_estimado: Optional[Decimal] = None
    total_recibido: Optional[Decimal] = None
    notas: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lineas: list[LineaOrdenCompraOut] = []

    model_config = {"from_attributes": True}
