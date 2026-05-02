"""Pedidos y líneas de pedido."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Date, Numeric, Enum, SmallInteger,
    Text, DateTime, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin, SoftDeleteMixin


class Pedido(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "pedidos"

    id = uuid_pk()
    tenant_id = tenant_fk()
    folio_interno = Column(String(20), index=True)
    contrato_lote_id = Column(UUID(as_uuid=True), ForeignKey("contratos_lotes.id"), nullable=True, index=True)
    cliente_facturacion_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)
    unidad_entrega_id = Column(UUID(as_uuid=True), ForeignKey("unidades_entrega.id"), nullable=True, index=True)

    fecha_pedido = Column(Date, nullable=False, index=True)
    fecha_entrega = Column(Date)
    estado = Column(
        Enum(
            "BORRADOR", "CONFIRMADO", "EN_SURTIDO", "ENVIADO", "ENTREGADO",
            "FACTURADO", "CANCELADO",
            name="pedido_estado",
        ),
        nullable=False, default="BORRADOR",
    )

    canal = Column(
        Enum(
            "WHATSAPP", "EMAIL", "EXCEL_BD", "LIBRETA_FOTO", "VOZ", "WEB", "API", "MANUAL",
            name="canal_origen",
        ),
        nullable=False,
    )
    raw_message_id = Column(UUID(as_uuid=True), ForeignKey("mensajes_log.id"), nullable=True)
    raw_payload = Column(JSONB)

    subtotal = Column(Numeric(18, 4), default=0)
    descuento = Column(Numeric(18, 4), default=0)
    iva = Column(Numeric(18, 4), default=0)
    total = Column(Numeric(18, 4), default=0)

    ai_confidence = Column(Numeric(5, 4))
    ai_warnings = Column(JSONB, default=list)
    requires_review = Column(Boolean, default=False, index=True)

    notas = Column(Text)
    custom_fields = Column(JSONB, default=dict)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    lineas = relationship("LineaPedido", back_populates="pedido", cascade="all, delete-orphan")


class LineaPedido(Base):
    __tablename__ = "lineas_pedido"
    __table_args__ = (UniqueConstraint("pedido_id", "numero_linea"),)

    id = uuid_pk()
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_linea = Column(SmallInteger, nullable=False)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=True)
    presentacion = Column(String(20), nullable=False, default="KILO")
    cantidad_solicitada = Column(Numeric(18, 4), nullable=False)
    cantidad_surtida = Column(Numeric(18, 4))
    precio_unitario = Column(Numeric(18, 4), nullable=False)
    importe = Column(Numeric(18, 4), nullable=False)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes_inventario.id"), nullable=True)
    texto_original = Column(Text)
    ai_match_confidence = Column(Numeric(5, 4))
    notas = Column(Text)

    pedido = relationship("Pedido", back_populates="lineas")
