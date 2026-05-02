from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ClienteBase(BaseModel):
    codigo: Optional[str] = None
    tipo: Literal["PRINCIPAL_GOV", "SUB", "PRIVADO", "OTRO"]
    legal_name: str
    rfc: str
    regimen_fiscal: Optional[str] = None
    uso_cfdi_default: Optional[str] = None
    forma_pago_default: Optional[str] = None
    metodo_pago_default: Optional[str] = None
    domicilio_fiscal: dict
    lista_precios_id: Optional[UUID] = None
    condiciones_pago: Optional[str] = None
    limite_credito: Decimal = Field(default=Decimal("0"))
    dias_credito: int = 0
    descuento_default: Decimal = Field(default=Decimal("0"))
    config_addenda: dict = {}
    custom_fields: dict = {}


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    legal_name: Optional[str] = None
    rfc: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    uso_cfdi_default: Optional[str] = None
    forma_pago_default: Optional[str] = None
    metodo_pago_default: Optional[str] = None
    domicilio_fiscal: Optional[dict] = None
    lista_precios_id: Optional[UUID] = None
    condiciones_pago: Optional[str] = None
    limite_credito: Optional[Decimal] = None
    dias_credito: Optional[int] = None
    descuento_default: Optional[Decimal] = None
    config_addenda: Optional[dict] = None
    custom_fields: Optional[dict] = None
    status: Optional[str] = None


class ClienteOut(ClienteBase):
    id: UUID
    tenant_id: UUID
    status: str
    saldo_actual: Decimal
    ventas_ytd: Decimal
    ultima_venta_at: Optional[datetime] = None
    ultimo_pago_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
