"""Proveedores y órdenes de compra (los 30 sub-sub)."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Date, Numeric, Enum, Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY

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

    id = uuid_pk()
    tenant_id = tenant_fk()
    folio = Column(String(20))
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("proveedores.id"), nullable=False, index=True)
    pedido_origen_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=True, index=True)
    fecha = Column(Date, nullable=False)
    estado = Column(
        Enum("BORRADOR", "ENVIADA", "ACEPTADA", "EN_TRANSITO", "RECIBIDA", "CANCELADA", name="oc_estado"),
        default="BORRADOR",
    )
    total_estimado = Column(Numeric(18, 4))
    notas = Column(Text)
