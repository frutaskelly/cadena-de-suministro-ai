from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.db import SessionLocal
from ...models import Tenant, User, Membership
from ...schemas import TenantCreate, TenantOut, UserCreate, UserOut, MembershipCreate, MembershipOut

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _db():
    """Session sin RLS (admin-level) — solo para crear tenants y onboarding."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=TenantOut, status_code=201)
def create_tenant(payload: TenantCreate, db: Session = Depends(_db)):
    if db.query(Tenant).filter(Tenant.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail=f"slug '{payload.slug}' ya existe")
    if db.query(Tenant).filter(Tenant.rfc == payload.rfc).first():
        raise HTTPException(status_code=409, detail=f"RFC '{payload.rfc}' ya existe")
    t = Tenant(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("", response_model=List[TenantOut])
def list_tenants(db: Session = Depends(_db)):
    return db.query(Tenant).filter(Tenant.deleted_at.is_(None)).all()


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: UUID, db: Session = Depends(_db)):
    t = db.get(Tenant, tenant_id)
    if not t or t.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return t


# ─── Users ──────────────────────────────────────────────────────────────────

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail=f"Email ya registrado")
    u = User(**payload.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@users_router.get("", response_model=List[UserOut])
def list_users(db: Session = Depends(_db)):
    return db.query(User).all()


# ─── Memberships ────────────────────────────────────────────────────────────

memberships_router = APIRouter(prefix="/memberships", tags=["memberships"])


@memberships_router.post("", response_model=MembershipOut, status_code=201)
def create_membership(payload: MembershipCreate, db: Session = Depends(_db)):
    existing = db.query(Membership).filter(
        Membership.tenant_id == payload.tenant_id,
        Membership.user_id == payload.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Membership ya existe")
    m = Membership(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@memberships_router.get("", response_model=List[MembershipOut])
def list_memberships(db: Session = Depends(_db)):
    return db.query(Membership).all()
