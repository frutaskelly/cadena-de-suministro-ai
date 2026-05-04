"""Proveedores, ordenes de compra y sus lineas."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Date, Numeric, Enum, Text,
    UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import relationship

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin


class Proveedor(Base, TimestampMixin):
    __tablename__ = "proveedores"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo"),)

    id = uuid_pk()
    tenant_id = tenant_fk()
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(254), nullable=False)
    rfc = Column(String(15))
    contacto = Column(String(254))
    telefono = Column(String(20))
    email = Column(String(254))
    categorias = Column(ARRAY(Text), default=list)
    contratos_lotes_atendidos = Column(ARRAY(UUID(as_uuid=True)), default=list)
    condiciones_pago = Column(String(50))
    activo = Column(Boolean, default=True)
    notas = Column(Text)


class OrdenCompra(Base, TimestampMixin):
    __tablename__ = "ordenes_compra"
    __table_args__ = (
        Index("ix_oc_proveedor", "proveedor_id"),
        Index("ix_oc_estado", "estado"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    folio = Column(String(20))
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("proveedores.id"), nullable=False, index=True)
    pedido_origen_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=True, index=True)
    almacen_destino_id = Column(UUID(as_uuid=True), ForeignKey("almacenes.id"), nullable=True)
    fecha = Column(Date, nullable=False)
    fecha_entrega_esperada = Column(Date, nullable=True)
    fecha_recibida = Column(Date, nullable=True)
    estado = Column(
        Enum(
            "BORRADOR", "ENVIADA", "ACEPTADA", "EN_TRANSITO",
            "RECIBIDA_PARCIAL", "RECIBIDA", "CANCELADA",
            name="oc_estado",
        ),
        default="BORRADOR",
    )
    subtotal = Column(Numeric(18, 4))
    iva_total = Column(Numeric(18, 4))
    total_estimado = Column(Numeric(18, 4))
    total_recibido = Column(Numeric(18, 4))
    notas = Column(Text)

    lineas = relationship(
        "LineaOrdenCompra",
        back_populates="orden",
        cascade="all, delete-orphan",
        order_by="LineaOrdenCompra.created_at",
    )


class LineaOrdenCompra(Base, TimestampMixin):
    """Linea de orden de compra (EHMO -> proveedor)."""
    __tablename__ = "lineas_orden_compra"
    __table_args__ = (
        Index("ix_loc_orden", "orden_compra_id"),
        Index("ix_loc_producto", "producto_id"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    orden_compra_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ordenes_compra.id", ondelete="CASCADE"),
        nullable=False,
    )
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)

    cantidad_solicitada = Column(Numeric(18, 4), nullable=False)
    cantidad_recibida = Column(Numeric(18, 4), nullable=False, default=0)
    presentacion = Column(String(50))

    precio_unitario = Column(Numeric(18, 4), nullable=False)
    importe = Column(Numeric(18, 4), nullable=False)

    notas = Column(Text)

    orden = relationship("OrdenCompra", back_populates="lineas")
