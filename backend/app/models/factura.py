"""CSDs, facturas, líneas de factura, pagos, abonos."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, BigInteger, Date, Numeric, Enum, Integer,
    SmallInteger, Text, DateTime, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin, SoftDeleteMixin


class CSD(Base):
    __tablename__ = "csds"

    id = uuid_pk()
    tenant_id = tenant_fk()
    numero_serie = Column(String(20), unique=True, nullable=False)
    vigencia_desde = Column(Date)
    vigencia_hasta = Column(Date)
    storage_path = Column(Text, nullable=False)
    password_kms_id = Column(Text, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Factura(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "facturas"
    __table_args__ = (UniqueConstraint("tenant_id", "serie", "folio", "tipo"),)

    id = uuid_pk()
    tenant_id = tenant_fk()
    serie = Column(String(10), nullable=False)
    folio = Column(BigInteger, nullable=False)
    tipo = Column(
        Enum("INGRESO", "EGRESO", "TRASLADO", "NOMINA", "PAGO", name="factura_tipo"),
        nullable=False, default="INGRESO",
    )
    estado = Column(
        Enum("BORRADOR", "TIMBRADA", "CANCELADA", "ERROR_TIMBRADO", name="factura_estado"),
        nullable=False, default="BORRADOR",
    )

    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=True, index=True)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)

    # Snapshot fiscal del receptor
    receptor_rfc = Column(String(15), nullable=False)
    receptor_nombre = Column(String(254), nullable=False)
    receptor_regimen = Column(String(4), nullable=False)
    receptor_uso_cfdi = Column(String(5), nullable=False)
    receptor_cp = Column(String(5), nullable=False)

    # Pago
    forma_pago = Column(String(5))
    metodo_pago = Column(String(5), nullable=False)
    moneda = Column(String(3), default="MXN")
    tipo_cambio = Column(Numeric(10, 6), default=1)
    condiciones_pago = Column(String(50))

    # Totales
    subtotal = Column(Numeric(18, 4), nullable=False)
    descuento = Column(Numeric(18, 4), default=0)
    iva_trasladado = Column(Numeric(18, 4), default=0)
    iva_retenido = Column(Numeric(18, 4), default=0)
    isr_retenido = Column(Numeric(18, 4), default=0)
    total = Column(Numeric(18, 4), nullable=False)

    # CFDI
    uuid_sat = Column(UUID(as_uuid=True), unique=True, index=True)
    fecha_timbrado = Column(DateTime(timezone=True))
    pac = Column(String(50))
    xml_storage_path = Column(Text)
    pdf_storage_path = Column(Text)
    certificado_sat = Column(String(20))

    # Cancelación
    fecha_cancelacion = Column(DateTime(timezone=True))
    motivo_cancelacion = Column(String(2))
    uuid_sustitucion = Column(UUID(as_uuid=True))
    acuse_cancelacion = Column(JSONB)

    # Addenda
    addenda_xml = Column(Text)

    custom_fields = Column(JSONB, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    lineas = relationship("LineaFactura", back_populates="factura", cascade="all, delete-orphan")


class LineaFactura(Base):
    __tablename__ = "lineas_factura"
    __table_args__ = (UniqueConstraint("factura_id", "numero_linea"),)

    id = uuid_pk()
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id", ondelete="CASCADE"), nullable=False, index=True)
    linea_pedido_id = Column(UUID(as_uuid=True), ForeignKey("lineas_pedido.id"), nullable=True)
    numero_linea = Column(SmallInteger, nullable=False)

    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=True)
    clave_sat = Column(String(8), nullable=False)
    unidad_sat = Column(String(3), nullable=False)
    objeto_imp = Column(String(2), nullable=False)
    descripcion = Column(Text, nullable=False)

    cantidad = Column(Numeric(18, 6), nullable=False)
    unidad_descripcion = Column(String(50))
    precio_unitario = Column(Numeric(18, 6), nullable=False)
    subtotal = Column(Numeric(18, 4), nullable=False)
    descuento = Column(Numeric(18, 4), default=0)
    iva_tasa = Column(Numeric(5, 4), default=0)
    iva_importe = Column(Numeric(18, 4), default=0)
    total_linea = Column(Numeric(18, 4), nullable=False)

    factura = relationship("Factura", back_populates="lineas")


class Pago(Base):
    __tablename__ = "pagos"

    id = uuid_pk()
    tenant_id = tenant_fk()
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    monto = Column(Numeric(18, 4), nullable=False)
    forma_pago = Column(String(5), nullable=False)
    banco = Column(String(100))
    referencia = Column(String(100))
    factura_pago_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=True)
    uuid_complemento = Column(UUID(as_uuid=True))
    notas = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class AbonoFactura(Base):
    __tablename__ = "abonos_factura"
    __table_args__ = (UniqueConstraint("pago_id", "factura_id", "numero_parcialidad"),)

    id = uuid_pk()
    pago_id = Column(UUID(as_uuid=True), ForeignKey("pagos.id"), nullable=False, index=True)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=False, index=True)
    monto = Column(Numeric(18, 4), nullable=False)
    numero_parcialidad = Column(Integer, nullable=False, default=1)
