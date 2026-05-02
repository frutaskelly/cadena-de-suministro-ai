"""Clientes (CRM con datos fiscales)."""
from sqlalchemy import (
    Column, String, ForeignKey, Numeric, Integer, Enum, UniqueConstraint, DateTime
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin, SoftDeleteMixin


class Cliente(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clientes"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo"),)

    id = uuid_pk()
    tenant_id = tenant_fk()
    codigo = Column(String(20))
    tipo = Column(
        Enum("PRINCIPAL_GOV", "SUB", "PRIVADO", "OTRO", name="cliente_tipo"),
        nullable=False,
    )
    status = Column(String(20), default="ACTIVO")

    # Fiscales
    legal_name = Column(String(254), nullable=False)
    rfc = Column(String(15), nullable=False, index=True)
    regimen_fiscal = Column(String(4))
    uso_cfdi_default = Column(String(5))
    forma_pago_default = Column(String(5))
    metodo_pago_default = Column(String(5))
    domicilio_fiscal = Column(JSONB, nullable=False, default=dict)

    # Comerciales
    lista_precios_id = Column(UUID(as_uuid=True), ForeignKey("listas_precios.id"), nullable=True)
    condiciones_pago = Column(String(50))
    limite_credito = Column(Numeric(18, 4), default=0)
    dias_credito = Column(Integer, default=0)
    descuento_default = Column(Numeric(5, 2), default=0)

    # Addenda
    config_addenda = Column(JSONB, default=dict)

    # Acumulados
    saldo_actual = Column(Numeric(18, 4), default=0)
    ventas_ytd = Column(Numeric(18, 4), default=0)
    ultima_venta_at = Column(DateTime(timezone=True))
    ultimo_pago_at = Column(DateTime(timezone=True))

    custom_fields = Column(JSONB, default=dict)
