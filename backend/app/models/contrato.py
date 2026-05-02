"""Contratos, lotes, unidades de entrega."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer, Date, Time, Enum,
    Numeric, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin, SoftDeleteMixin


class Contrato(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contratos"

    id = uuid_pk()
    tenant_id = tenant_fk()
    numero_contrato = Column(String(50))
    contratante = Column(String(254), nullable=False)
    contratante_rfc = Column(String(15))
    estado_mx = Column(String(50))
    vigencia_desde = Column(Date, nullable=False)
    vigencia_hasta = Column(Date, nullable=False)
    monto_max = Column(Numeric(18, 4))
    condiciones_pago = Column(String(50))
    notas = Column(Text)
    config = Column(JSONB, default=dict)

    lotes = relationship("ContratoLote", back_populates="contrato", cascade="all, delete-orphan")
    unidades = relationship("UnidadEntrega", back_populates="contrato", cascade="all, delete-orphan")


class ContratoLote(Base, TimestampMixin):
    __tablename__ = "contratos_lotes"
    __table_args__ = (UniqueConstraint("contrato_id", "numero_lote"),)

    id = uuid_pk()
    contrato_id = Column(UUID(as_uuid=True), ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False)
    numero_lote = Column(Integer, nullable=False)
    descripcion = Column(String(254), nullable=False)
    asignado_a_tenant = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    lista_precios_id = Column(UUID(as_uuid=True), ForeignKey("listas_precios.id"), nullable=True)
    monto_lote = Column(Numeric(18, 4))

    contrato = relationship("Contrato", back_populates="lotes")


class UnidadEntrega(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "unidades_entrega"

    id = uuid_pk()
    contrato_id = Column(UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=False, index=True)
    codigo = Column(String(50))
    nombre = Column(String(254), nullable=False)
    tipo = Column(
        Enum("HOSPITAL", "COMEDOR", "ESCUELA", "MILITAR", "RECLUSORIO", "ALMACEN", "OTRO", name="unidad_tipo"),
        nullable=False,
    )
    ciudad = Column(String(100))
    estado_mx = Column(String(50))
    direccion = Column(Text)
    cp = Column(String(5))
    contacto_nombre = Column(String(254))
    contacto_telefono = Column(String(20))
    contacto_email = Column(String(254))
    geo_lat = Column(Numeric(10, 7))
    geo_lon = Column(Numeric(10, 7))
    frecuencia_entrega = Column(String(50))
    hora_corte_pedido = Column(Time)
    hora_entrega = Column(Time)
    protocolo = Column(JSONB, default=dict)
    activa = Column(Boolean, default=True)
    notas = Column(Text)

    contrato = relationship("Contrato", back_populates="unidades")
