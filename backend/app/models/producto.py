"""Productos, listas de precios, precios."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer, Date, Numeric, Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin, SoftDeleteMixin


class Producto(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "productos"
    __table_args__ = (UniqueConstraint("tenant_id", "sku_interno"),)

    id = uuid_pk()
    tenant_id = tenant_fk()
    sku_interno = Column(String(50), nullable=False)
    nombre = Column(String(254), nullable=False)
    nombre_normalizado = Column(String(254), index=True)
    descripcion = Column(Text)
    categoria = Column(String(100))
    lote_default = Column(Integer, default=5)

    # Sprint 8: clasificacion extendida
    categoria_extendida = Column(String(40), nullable=True)
    # Valores tipicos:
    # FRUTAS_VERDURAS, LACTEOS_EMBUTIDOS, PROTEINA_ANIMAL, TORTILLAS, PAN,
    # GRANOS_SEMILLAS, ABARROTE, AGUA, REFRESCO, LIMPIEZA, DESECHABLES, OTRO
    es_catalogado = Column(Boolean, default=True, nullable=False, server_default="true")
    perecedero = Column(Boolean, default=False, nullable=False, server_default="false")
    cold_chain = Column(Boolean, default=False, nullable=False, server_default="false")
    requiere_lote = Column(Boolean, default=False, nullable=False, server_default="false")
    requiere_caducidad = Column(Boolean, default=False, nullable=False, server_default="false")
    vida_util_dias = Column(Integer, nullable=True)

    # SAT
    clave_sat = Column(String(8), nullable=False)
    unidad_sat = Column(String(3), nullable=False)
    objeto_imp = Column(String(2), default="02")
    iva_tasa = Column(Numeric(5, 4), default=0)
    ieps_tasa = Column(Numeric(5, 4), default=0)

    # Presentaciones (JSON: {"KILO": 1, "BULTO_25K": 25, ...})
    presentaciones = Column(JSONB, default=lambda: {"KILO": 1})
    presentacion_default = Column(String(20), default="KILO")

    # Sinónimos / aliases
    sinonimos = Column(ARRAY(Text), default=list)
    aliases_clientes = Column(JSONB, default=dict)

    costo_promedio = Column(Numeric(18, 4), default=0)
    activo = Column(Boolean, default=True)
    custom_fields = Column(JSONB, default=dict)


class ListaPrecios(Base, TimestampMixin):
    __tablename__ = "listas_precios"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo"),)

    id = uuid_pk()
    tenant_id = tenant_fk()
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(254), nullable=False)
    vigencia_desde = Column(Date)
    vigencia_hasta = Column(Date)
    moneda = Column(String(3), default="MXN")
    notas = Column(Text)


class Precio(Base):
    __tablename__ = "precios"
    __table_args__ = (
        UniqueConstraint("lista_id", "producto_id", "presentacion", "vigencia_desde"),
    )

    id = uuid_pk()
    lista_id = Column(UUID(as_uuid=True), ForeignKey("listas_precios.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False, index=True)
    presentacion = Column(String(20), nullable=False, default="KILO")
    precio_unitario = Column(Numeric(18, 4), nullable=False)
    vigencia_desde = Column(Date)
    vigencia_hasta = Column(Date)
