"""Remisiones (entregas pendientes de facturar) y ajustes en sitio.

Modelo del inventario triple-estado:
- INVENTARIO_FISICO: lotes_inventario.cantidad_disponible
- REMISION_PENDIENTE: lotes_inventario.cantidad_reservada (suma de lineas_remision activas)
- VENTA_FACTURADA: facturas + lineas_factura ligadas a la remision

Ecuacion maestra:
    fisico = compras_recibidas - ventas_facturadas - remisiones_pendientes - mermas - ajustes
"""
from sqlalchemy import (
    Column, String, ForeignKey, Date, DateTime, Numeric, Enum,
    Text, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin


class Remision(Base, TimestampMixin):
    """Entrega fisica al cliente, en estado pendiente de facturar.

    Una remision puede convertirse en factura (estado FACTURADA) o cancelarse.
    """
    __tablename__ = "remisiones"
    __table_args__ = (
        UniqueConstraint("tenant_id", "folio", name="uq_remision_folio"),
        Index("ix_remision_pedido", "pedido_id"),
        Index("ix_remision_cliente", "cliente_id"),
        Index("ix_remision_estado", "estado"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    folio = Column(String(20), nullable=False)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=True, index=True)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)
    unidad_entrega_id = Column(UUID(as_uuid=True), ForeignKey("unidades_entrega.id"), nullable=True, index=True)
    almacen_origen_id = Column(UUID(as_uuid=True), ForeignKey("almacenes.id"), nullable=True, index=True)

    fecha_generada = Column(Date, nullable=False, server_default=func.current_date())
    fecha_entrega = Column(DateTime(timezone=True), nullable=True)
    fecha_facturada = Column(DateTime(timezone=True), nullable=True)

    estado = Column(
        Enum(
            "GENERADA",       # creada, antes de salir
            "EN_TRANSITO",    # ya salio del almacen
            "ENTREGADA",      # llego al cliente, esperando confirmacion
            "CONFIRMADA",     # cliente confirmo entrega; lista para facturar
            "FACTURADA",      # ya tiene CFDI emitido
            "CANCELADA",      # rechazada o cancelada
            name="remision_estado",
        ),
        nullable=False,
        default="GENERADA",
    )

    # vinculo a factura (cuando estado=FACTURADA)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=True, index=True)

    subtotal = Column(Numeric(18, 4), nullable=True)
    iva_total = Column(Numeric(18, 4), nullable=True)
    total = Column(Numeric(18, 4), nullable=True)

    notas = Column(Text)
    raw_payload = Column(JSONB)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    lineas = relationship(
        "LineaRemision",
        back_populates="remision",
        cascade="all, delete-orphan",
        order_by="LineaRemision.created_at",
    )


class LineaRemision(Base, TimestampMixin):
    """Linea de remision: lo que se entrego (puede diferir de lo pedido)."""
    __tablename__ = "lineas_remision"
    __table_args__ = (
        Index("ix_linea_remision_remision", "remision_id"),
        Index("ix_linea_remision_producto", "producto_id"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    remision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("remisiones.id", ondelete="CASCADE"),
        nullable=False,
    )

    # vinculos al pedido original (si existe)
    linea_pedido_id = Column(UUID(as_uuid=True), ForeignKey("lineas_pedido.id"), nullable=True)

    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    lote_inventario_id = Column(UUID(as_uuid=True), ForeignKey("lotes_inventario.id"), nullable=True)

    # cantidades en los 3 estados
    cantidad_solicitada = Column(Numeric(18, 4), nullable=False, default=0)
    cantidad_entregada = Column(Numeric(18, 4), nullable=False)
    cantidad_facturada = Column(Numeric(18, 4), nullable=True)  # se llena al facturar

    presentacion = Column(String(50))
    precio_unitario = Column(Numeric(18, 4), nullable=False)
    importe = Column(Numeric(18, 4), nullable=False)

    # razon de cambio
    motivo_ajuste = Column(String(254))

    remision = relationship("Remision", back_populates="lineas")


class AjusteRemision(Base):
    """Bitacora de ajustes en remisiones (peso, cancelacion, sustitucion).

    Append-only: cada cambio en linea_remision durante o post-entrega genera
    una entrada aqui.
    """
    __tablename__ = "ajustes_remision"
    __table_args__ = (
        Index("ix_ajuste_remision", "remision_id"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    remision_id = Column(UUID(as_uuid=True), ForeignKey("remisiones.id"), nullable=False)
    linea_remision_id = Column(UUID(as_uuid=True), ForeignKey("lineas_remision.id"), nullable=True)

    tipo = Column(
        Enum(
            "PESO",            # peso real difiere del pedido
            "CANTIDAD",        # cantidad ajustada
            "CANCELACION",     # linea cancelada
            "SUSTITUCION",     # cambio de producto (catalogado <-> no-catalogado)
            "PRECIO",          # ajuste de precio
            name="ajuste_remision_tipo",
        ),
        nullable=False,
    )

    cantidad_anterior = Column(Numeric(18, 4))
    cantidad_nueva = Column(Numeric(18, 4))
    precio_anterior = Column(Numeric(18, 4))
    precio_nuevo = Column(Numeric(18, 4))
    producto_anterior_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=True)
    producto_nuevo_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=True)

    motivo = Column(Text)

    requiere_aprobacion = Column(String(10), default="NO")  # NO, PENDIENTE, APROBADO, RECHAZADO
    aprobado_por = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    aprobado_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
