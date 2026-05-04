"""Conversiones entre productos catalogados y no-catalogados (Sprint 8).

Concepto:
- Hospital factura "Manzana Roja" (catalogada).
- Bodega tiene "Manzana Royal Gala" (no-catalogada).
- Conversion mapea: 1 kg manzana_roja_catalogada = factor x kg manzana_royal_gala
  con merma_pct opcional, precio_no_cat opcional.
- mezcla_grupo_id permite que N no-cats juntos cubran 1 cat (ej. mix de manzanas).
"""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer, Numeric, Text,
    UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin


class ConversionProducto(Base, TimestampMixin):
    """Mapeo de producto no-catalogado a producto catalogado para sustitucion."""
    __tablename__ = "conversiones_producto"
    __table_args__ = (
        Index("ix_conv_cat", "producto_catalogado_id"),
        Index("ix_conv_no_cat", "producto_no_catalogado_id"),
        Index("ix_conv_grupo", "mezcla_grupo_id"),
        UniqueConstraint(
            "tenant_id",
            "producto_catalogado_id",
            "producto_no_catalogado_id",
            name="uq_conv_par",
        ),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()

    producto_catalogado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("productos.id"),
        nullable=False,
    )
    producto_no_catalogado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("productos.id"),
        nullable=False,
    )

    # qty no_cat necesaria para 1 unidad de cat (despues de merma)
    factor = Column(Numeric(18, 6), nullable=False, default=1, server_default="1")
    # porcentaje de merma esperada (0.05 = 5%)
    merma_pct = Column(Numeric(7, 4), nullable=False, default=0, server_default="0")

    # precio override del no_cat (si distinto del cat)
    precio_no_cat = Column(Numeric(18, 4), nullable=True)

    # mezcla: N no_cats agrupados que juntos cubren 1 cat
    mezcla_grupo_id = Column(UUID(as_uuid=True), nullable=True)
    mezcla_proporcion = Column(Numeric(7, 4), nullable=True)
    # ej: 0.4 = 40% de la conversion viene de este no_cat

    prioridad = Column(Integer, default=10, nullable=False, server_default="10")
    requiere_aprobacion = Column(Boolean, default=False, nullable=False, server_default="false")
    activo = Column(Boolean, default=True, nullable=False, server_default="true")
    notas = Column(Text)
