from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProductoBase(BaseModel):
    sku_interno: str
    nombre: str
    nombre_normalizado: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    lote_default: int = 5
    clave_sat: str = "01010101"  # generic placeholder; AI classify later
    unidad_sat: str = "KGM"
    objeto_imp: str = "02"
    iva_tasa: Decimal = Field(default=Decimal("0"))
    ieps_tasa: Decimal = Field(default=Decimal("0"))
    presentaciones: dict = {"KILO": 1}
    presentacion_default: str = "KILO"
    sinonimos: list[str] = []
    aliases_clientes: dict = {}
    activo: bool = True
    custom_fields: dict = {}


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    clave_sat: Optional[str] = None
    unidad_sat: Optional[str] = None
    iva_tasa: Optional[Decimal] = None
    presentaciones: Optional[dict] = None
    sinonimos: Optional[list[str]] = None
    aliases_clientes: Optional[dict] = None
    activo: Optional[bool] = None


class ProductoOut(ProductoBase):
    id: UUID
    tenant_id: UUID
    costo_promedio: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ListaPreciosBase(BaseModel):
    codigo: str
    nombre: str
    vigencia_desde: Optional[date] = None
    vigencia_hasta: Optional[date] = None
    moneda: str = "MXN"
    notas: Optional[str] = None


class ListaPreciosCreate(ListaPreciosBase):
    pass


class ListaPreciosOut(ListaPreciosBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PrecioCreate(BaseModel):
    lista_id: UUID
    producto_id: UUID
    presentacion: str = "KILO"
    precio_unitario: Decimal
    vigencia_desde: Optional[date] = None
    vigencia_hasta: Optional[date] = None


class PrecioOut(PrecioCreate):
    id: UUID

    model_config = {"from_attributes": True}
