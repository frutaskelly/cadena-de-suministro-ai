"""Schemas Pydantic para remisiones, lineas, y ajustes."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


# ---------- Lineas ----------
class LineaRemisionCreate(BaseModel):
    producto_id: UUID
    linea_pedido_id: Optional[UUID] = None
    lote_inventario_id: Optional[UUID] = None
    cantidad_solicitada: Decimal = Decimal(0)
    cantidad_entregada: Decimal
    presentacion: Optional[str] = None
    precio_unitario: Decimal
    importe: Decimal
    motivo_ajuste: Optional[str] = None


class LineaRemisionOut(LineaRemisionCreate):
    id: UUID
    remision_id: UUID
    cantidad_facturada: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Remisiones ----------
class RemisionCreate(BaseModel):
    folio: str
    pedido_id: Optional[UUID] = None
    cliente_id: UUID
    unidad_entrega_id: Optional[UUID] = None
    almacen_origen_id: Optional[UUID] = None
    fecha_generada: Optional[date] = None
    estado: Literal[
        "GENERADA", "EN_TRANSITO", "ENTREGADA",
        "CONFIRMADA", "FACTURADA", "CANCELADA",
    ] = "GENERADA"
    notas: Optional[str] = None
    raw_payload: Optional[dict] = None
    lineas: list[LineaRemisionCreate] = []


class RemisionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    folio: str
    pedido_id: Optional[UUID] = None
    cliente_id: UUID
    unidad_entrega_id: Optional[UUID] = None
    almacen_origen_id: Optional[UUID] = None
    fecha_generada: date
    fecha_entrega: Optional[datetime] = None
    fecha_facturada: Optional[datetime] = None
    estado: str
    factura_id: Optional[UUID] = None
    subtotal: Optional[Decimal] = None
    iva_total: Optional[Decimal] = None
    total: Optional[Decimal] = None
    notas: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lineas: list[LineaRemisionOut] = []

    model_config = {"from_attributes": True}


# ---------- Ajustes ----------
class AjusteRemisionCreate(BaseModel):
    remision_id: UUID
    linea_remision_id: Optional[UUID] = None
    tipo: Literal["PESO", "CANTIDAD", "CANCELACION", "SUSTITUCION", "PRECIO"]
    cantidad_anterior: Optional[Decimal] = None
    cantidad_nueva: Optional[Decimal] = None
    precio_anterior: Optional[Decimal] = None
    precio_nuevo: Optional[Decimal] = None
    producto_anterior_id: Optional[UUID] = None
    producto_nuevo_id: Optional[UUID] = None
    motivo: Optional[str] = None
    requiere_aprobacion: Literal["NO", "PENDIENTE", "APROBADO", "RECHAZADO"] = "NO"


class AjusteRemisionOut(AjusteRemisionCreate):
    id: UUID
    tenant_id: UUID
    aprobado_por: Optional[UUID] = None
    aprobado_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Inventario triple-estado snapshot ----------
class InventarioTripleEstado(BaseModel):
    """Vista del inventario en sus 3 estados simultaneos."""
    producto_id: UUID
    producto_nombre: str
    almacen_id: UUID
    cantidad_fisica: Decimal      # disponible en bodega
    cantidad_remision: Decimal    # comprometida en remisiones pendientes
    cantidad_facturada_acumulada: Decimal  # vendida facturada (historico)
    total_disponible_efectivo: Decimal  # fisica - remision
