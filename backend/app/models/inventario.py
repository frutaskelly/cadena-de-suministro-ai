"""Almacenes, lotes inventario, movimientos, mermas."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Date, DateTime, Numeric, Enum,
    Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin


class Almacen(Base, TimestampMixin):
    __tablename__ = "almacenes"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo"),)

    id = uuid_pk()
    tenant_id = tenant_fk()
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(254), nullable=False)
    direccion = Column(Text)
    es_default = Column(Boolean, default=False)


class LoteInventario(Base, TimestampMixin):
    """Lote de inventario.

    Triple-estado:
    - cantidad_disponible: fisicamente en bodega disponible para venta
    - cantidad_reservada: comprometida en remisiones pendientes de facturar
    - (facturado se calcula via movimientos_inventario tipo SALIDA_FACTURADA)
    """
    __tablename__ = "lotes_inventario"

    id = uuid_pk()
    tenant_id = tenant_fk()
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False, index=True)
    almacen_id = Column(UUID(as_uuid=True), ForeignKey("almacenes.id"), nullable=False, index=True)
    numero_lote = Column(String(50))
    fecha_ingreso = Column(Date, nullable=False)
    fecha_caducidad = Column(Date, index=True)
    cantidad_inicial = Column(Numeric(18, 4), nullable=False)
    cantidad_disponible = Column(Numeric(18, 4), nullable=False)
    cantidad_reservada = Column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    costo_unitario = Column(Numeric(18, 4), nullable=False)
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("proveedores.id"), nullable=True)
    orden_compra_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_compra.id"), nullable=True)
    notas = Column(Text)


class MovimientoInventario(Base):
    """Bitacora append-only de cambios de inventario.

    Tipos:
    - ENTRADA_COMPRA: orden de compra recibida -> aumenta disponible
    - SALIDA_REMISION: remision generada -> disponible -> reservada
    - CONFIRMACION_FACTURA: remision facturada -> reservada -> 0 (sale)
    - CANCELACION_REMISION: remision cancelada -> reservada -> disponible
    - AJUSTE: correccion manual
    - MERMA: producto descartado
    - TRANSFERENCIA: entre almacenes
    """
    __tablename__ = "movimientos_inventario"

    id = uuid_pk()
    tenant_id = tenant_fk()
    tipo = Column(
        Enum(
            "ENTRADA",                 # legacy: usar ENTRADA_COMPRA preferentemente
            "SALIDA",                  # legacy
            "AJUSTE",
            "MERMA",
            "TRANSFERENCIA",
            "ENTRADA_COMPRA",          # Sprint 7: compra recibida
            "SALIDA_REMISION",         # Sprint 7: remision generada
            "CONFIRMACION_FACTURA",    # Sprint 7: remision facturada
            "CANCELACION_REMISION",    # Sprint 7: remision cancelada
            name="movimiento_tipo",
        ),
        nullable=False,
    )
    fecha = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes_inventario.id"), nullable=False, index=True)
    cantidad = Column(Numeric(18, 4), nullable=False)
    costo_unitario = Column(Numeric(18, 4))
    ref_tipo = Column(String(20))
    ref_id = Column(UUID(as_uuid=True), index=True)
    motivo = Column(String(254))
    notas = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Merma(Base):
    __tablename__ = "mermas"

    id = uuid_pk()
    tenant_id = tenant_fk()
    fecha = Column(Date, nullable=False)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes_inventario.id"), nullable=False)
    cantidad = Column(Numeric(18, 4), nullable=False)
    motivo = Column(
        Enum("CADUCIDAD", "CALIDAD", "DEVOLUCION_CLIENTE", "ROBO", "DESCOMPOSICION", "OTRO", name="merma_motivo"),
        nullable=False,
    )
    descripcion = Column(Text)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=True)
    evidencia_url = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
