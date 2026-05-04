"""Modelos del modulo WhatsApp / Agentes / Documentos generados (Sprint 9)."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer, Date, DateTime,
    Text, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, tenant_fk, TimestampMixin


class AgenteWhatsapp(Base, TimestampMixin):
    """Configuracion de cada agente WhatsApp del sistema (legacy v1).

    Cada agente atiende un cliente fiscal con su lista de precios y
    cuenta con su propio contador de folios.
    """
    __tablename__ = "agentes_whatsapp"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo"),
        Index("ix_agente_cliente", "cliente_id"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    codigo = Column(String(40), nullable=False)  # "ehmo_hospitales", "surena_comedores", etc.
    nombre = Column(String(254), nullable=False)
    descripcion = Column(Text)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    lista_precios_id = Column(UUID(as_uuid=True), ForeignKey("listas_precios.id"), nullable=True)
    tipo = Column(String(40), nullable=False)  # "hospitales", "comedores", "dif", etc.
    icono = Column(String(10))
    color_hex = Column(String(10))
    activo = Column(Boolean, default=True, nullable=False)

    # contador de folios secuencial
    proximo_folio = Column(Integer, default=1, nullable=False)
    requires_pesos = Column(Boolean, default=False, nullable=False)

    # configuracion / system_prompt addendum / etc.
    config = Column(JSONB, default=dict, nullable=False, server_default="{}")
    system_prompt_addendum = Column(Text)


class DocumentoGenerado(Base):
    """Documentos generados por el agente (PDFs, XLSX) en el flujo legacy.

    Tipos:
    - PEDIDO_PDF / PEDIDO_XLSX: documento de surtido para almacen
    - LISTA_COMPRAS_PDF / LISTA_COMPRAS_XLSX: lista consolidada de compras
    - REMISION_PDF: nota de remision por cliente
    - RELACION_PDF: relacion total de notas del dia
    """
    __tablename__ = "documentos_generados"
    __table_args__ = (
        Index("ix_doc_tipo", "tipo_documento"),
        Index("ix_doc_remision", "remision_id"),
        Index("ix_doc_pedido", "pedido_id"),
        Index("ix_doc_fecha", "fecha_documento"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()

    agente_id = Column(UUID(as_uuid=True), ForeignKey("agentes_whatsapp.id"), nullable=True)
    remision_id = Column(UUID(as_uuid=True), ForeignKey("remisiones.id"), nullable=True)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=True)

    tipo_documento = Column(
        String(40),
        nullable=False,
    )  # PEDIDO_PDF, PEDIDO_XLSX, LISTA_COMPRAS_PDF, LISTA_COMPRAS_XLSX, REMISION_PDF, RELACION_PDF
    nombre_archivo = Column(String(254), nullable=False)
    fecha_documento = Column(Date)
    url_storage = Column(Text)  # Supabase Storage path o Drive URL
    sha256 = Column(String(64))  # hash del contenido para integridad
    bytes = Column(Integer)

    # contexto: que destinos cubre, que folios contiene, etc.
    metadata_doc = Column("metadata", JSONB, default=dict, nullable=False, server_default="{}")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
