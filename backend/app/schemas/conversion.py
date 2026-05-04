"""Schemas para conversiones producto catalogado <-> no-catalogado."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ConversionCreate(BaseModel):
    producto_catalogado_id: UUID
    producto_no_catalogado_id: UUID
    factor: Decimal = Decimal("1")
    merma_pct: Decimal = Decimal("0")
    precio_no_cat: Optional[Decimal] = None
    mezcla_grupo_id: Optional[UUID] = None
    mezcla_proporcion: Optional[Decimal] = None
    prioridad: int = 10
    requiere_aprobacion: bool = False
    activo: bool = True
    notas: Optional[str] = None


class ConversionUpdate(BaseModel):
    factor: Optional[Decimal] = None
    merma_pct: Optional[Decimal] = None
    precio_no_cat: Optional[Decimal] = None
    mezcla_grupo_id: Optional[UUID] = None
    mezcla_proporcion: Optional[Decimal] = None
    prioridad: Optional[int] = None
    requiere_aprobacion: Optional[bool] = None
    activo: Optional[bool] = None
    notas: Optional[str] = None


class ConversionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    producto_catalogado_id: UUID
    producto_no_catalogado_id: UUID
    factor: Decimal
    merma_pct: Decimal
    precio_no_cat: Optional[Decimal] = None
    mezcla_grupo_id: Optional[UUID] = None
    mezcla_proporcion: Optional[Decimal] = None
    prioridad: int
    requiere_aprobacion: bool
    activo: bool
    notas: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
