"""Tenants, users, memberships."""
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer, Date, Enum,
    DateTime, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.db import Base
from .base import uuid_pk, TimestampMixin, SoftDeleteMixin


class Tenant(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"

    id = uuid_pk()
    parent_tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    tier = Column(Enum("PRINCIPAL", "SUB", "SUB_SUB", name="tenant_tier"), nullable=False)
    status = Column(
        Enum("ACTIVE", "TRIAL", "SUSPENDED", "CHURNED", name="tenant_status"),
        nullable=False, default="TRIAL",
    )
    slug = Column(String(50), unique=True, nullable=False)
    legal_name = Column(String(254), nullable=False)
    trade_name = Column(String(254))
    rfc = Column(String(15), unique=True, nullable=False)
    regimen_fiscal_sat = Column(String(4), nullable=False)
    domicilio_fiscal_cp = Column(String(5), nullable=False)
    domicilio_fiscal = Column(JSONB, nullable=False, default=dict)
    config = Column(JSONB, default=dict)
    plan = Column(String(50), default="trial")
    seats_limit = Column(Integer, default=3)
    trial_ends_at = Column(Date)

    parent = relationship("Tenant", remote_side="Tenant.id")


class User(Base):
    __tablename__ = "users"

    id = uuid_pk()
    email = Column(String(254), unique=True, nullable=False, index=True)
    full_name = Column(String(254))
    phone = Column(String(20))
    auth_provider = Column(String(20), default="supabase")
    auth_user_id = Column(String(254), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id"),)

    id = uuid_pk()
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(
        Enum("OWNER", "ADMIN", "OPERATOR", "VIEWER", name="user_role"),
        nullable=False,
    )
    active = Column(Boolean, default=True)

    tenant = relationship("Tenant")
    user = relationship("User")
