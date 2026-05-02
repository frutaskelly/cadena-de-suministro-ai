from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel


class LineaPedidoCreate(BaseModel):
    numero_linea: int
    producto_id: Optional[UUID] = None
    presentacion: str = "KILO"
    cantidad_solicitada: Decimal
    cantidad_surtida: Optional[Decimal] = None
    precio_unitario: Decimal
    importe: Decimal
    texto_original: Optional[str] = None
    ai_match_confidence: Optional[Decimal] = None
    notas: Optional[str] = None


class LineaPedidoOut(LineaPedidoCreate):
    id: UUID
    pedido_id: UUID

    model_config = {"from_attributes": True}


class PedidoBase(BaseModel):
    folio_interno: Optional[str] = None
    contrato_lote_id: Optional[UUID] = None
    cliente_facturacion_id: UUID
    unidad_entrega_id: Optional[UUID] = None
    fecha_pedido: date
    fecha_entrega: Optional[date] = None
    estado: Literal[
        "BORRADOR", "CONFIRMADO", "EN_SURTIDO", "ENVIADO", "ENTREGADO",
        "FACTURADO", "CANCELADO",
    ] = "BORRADOR"
    canal: Literal["WHATSAPP", "EMAIL", "EXCEL_BD", "LIBRETA_FOTO", "VOZ", "WEB", "API", "MANUAL"]
    raw_payload: Optional[dict] = None
    ai_confidence: Optional[Decimal] = None
    ai_warnings: list = []
    requires_review: bool = False
    notas: Optional[str] = None
    custom_fields: dict = {}


class PedidoCreate(PedidoBase):
    lineas: list[LineaPedidoCreate] = []


class PedidoOut(PedidoBase):
    id: UUID
    tenant_id: UUID
    subtotal: Decimal
    descuento: Decimal
    iva: Decimal
    total: Decimal
    created_at: datetime
    updated_at: datetime
    lineas: list[LineaPedidoOut] = []

    model_config = {"from_attributes": True}
