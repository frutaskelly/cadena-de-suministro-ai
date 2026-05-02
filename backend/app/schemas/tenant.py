from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class TenantBase(BaseModel):
    tier: Literal["PRINCIPAL", "SUB", "SUB_SUB"]
    slug: str = Field(..., min_length=2, max_length=50)
    legal_name: str
    trade_name: Optional[str] = None
    rfc: str = Field(..., min_length=12, max_length=15)
    regimen_fiscal_sat: str
    domicilio_fiscal_cp: str
    domicilio_fiscal: dict


class TenantCreate(TenantBase):
    parent_tenant_id: Optional[UUID] = None
    config: dict = {}


class TenantOut(TenantBase):
    id: UUID
    parent_tenant_id: Optional[UUID] = None
    status: str
    plan: str
    seats_limit: int
    trial_ends_at: Optional[date] = None
    config: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipCreate(BaseModel):
    tenant_id: UUID
    user_id: UUID
    role: Literal["OWNER", "ADMIN", "OPERATOR", "VIEWER"]


class MembershipOut(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str
    active: bool

    model_config = {"from_attributes": True}
