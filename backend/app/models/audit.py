"""Audit log inmutable de decisiones AI + jobs de Base Maestra (Sprint 13).

ai_decisions: cada vez que el AI hace una transformacion / decision
relevante (extraer accion, matchear producto, validar output, etc.)
guardamos input + output + confidence + modelo. Si despues se descubre
un error, se puede auditar.

base_maestra_runs: track de cada generacion de Base Maestra con stats,
hospitales OK/fallidos, link Drive, diff vs anterior.
"""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer, DateTime,
    Text, Index, Numeric,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, tenant_fk


class AiDecision(Base):
    """Append-only log de decisiones del AI."""
    __tablename__ = "ai_decisions"
    __table_args__ = (
        Index("ix_ai_decisions_tenant", "tenant_id"),
        Index("ix_ai_decisions_tipo", "tipo"),
        Index("ix_ai_decisions_ref", "ref_tipo", "ref_id"),
        Index("ix_ai_decisions_created", "created_at"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()
    tipo = Column(String(40), nullable=False)
    # tipos: extract_action, match_producto, match_unidad, validate_base_maestra,
    #        classify_clave_sat, parse_libreta, parse_excel_bd, ...

    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB)
    confidence = Column(Numeric(5, 4))  # 0.0000 - 1.0000
    aprobado = Column(Boolean)
    requires_review = Column(Boolean, default=False, nullable=False, server_default="false")

    model_used = Column(String(60))
    prompt_version = Column(String(20))
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    elapsed_ms = Column(Integer)

    ref_tipo = Column(String(40))  # "pedido", "remision", "producto", "base_maestra_run"
    ref_id = Column(UUID(as_uuid=True))

    conversacion_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversaciones.id"), nullable=True)
    mensaje_id = Column(UUID(as_uuid=True), ForeignKey("chat_mensajes.id"), nullable=True)

    error = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class BaseMaestraRun(Base):
    """Track de cada generacion de Base Maestra."""
    __tablename__ = "base_maestra_runs"
    __table_args__ = (
        Index("ix_bm_runs_tenant", "tenant_id"),
        Index("ix_bm_runs_fecha", "fecha_inicio"),
    )

    id = uuid_pk()
    tenant_id = tenant_fk()

    fecha_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=False)
    semana_label = Column(String(60))  # "4 al 10 de mayo 2026"

    estado = Column(
        String(20), nullable=False, default="EN_PROGRESO",
    )  # EN_PROGRESO, EXITOSA, EXITOSA_CON_WARNINGS, FALLIDA

    # Input
    source_folder = Column(Text)  # path o descripcion
    archivos_count = Column(Integer, default=0, nullable=False)

    # Resultados
    hospitales_ok = Column(Integer, default=0)
    hospitales_warning = Column(Integer, default=0)
    hospitales_fallidos = Column(Integer, default=0)
    filas_bd = Column(Integer, default=0)
    productos_no_match = Column(Integer, default=0)

    # Output
    output_local_path = Column(Text)
    output_drive_url = Column(Text)
    output_size_bytes = Column(Integer)

    # Validation
    diff_pct_vs_anterior = Column(Numeric(7, 4))  # ej. 0.05 = 5% diferencia
    ai_validation_passed = Column(Boolean)
    ai_validation_notes = Column(Text)

    # Reporte detallado por hospital
    detalle = Column(JSONB)
    # shape: [{"hospital": "...", "estado": "OK|WARN|FAIL",
    #          "filas": 314, "warnings": [...], "errors": [...]}]

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at = Column(DateTime(timezone=True))
    elapsed_ms = Column(Integer)

    conversacion_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversaciones.id"), nullable=True)
