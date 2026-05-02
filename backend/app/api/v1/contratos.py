from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db_session, require_tenant
from ...models import Contrato, ContratoLote, UnidadEntrega
from ...schemas import (
    ContratoCreate, ContratoOut,
    ContratoLoteCreate, ContratoLoteOut,
    UnidadEntregaCreate, UnidadEntregaOut,
)

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.post("", response_model=ContratoOut, status_code=201)
def create_contrato(
    payload: ContratoCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    c = Contrato(**payload.model_dump(), tenant_id=tenant_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("", response_model=List[ContratoOut])
def list_contratos(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    return db.query(Contrato).filter(
        Contrato.tenant_id == tenant_id,
        Contrato.deleted_at.is_(None),
    ).order_by(Contrato.contratante).all()


@router.get("/{contrato_id}", response_model=ContratoOut)
def get_contrato(
    contrato_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    c = db.query(Contrato).filter(
        Contrato.id == contrato_id,
        Contrato.tenant_id == tenant_id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return c


# ─── Lotes ──────────────────────────────────────────────────────────────────

lotes_router = APIRouter(prefix="/contrato-lotes", tags=["contratos"])


@lotes_router.post("", response_model=ContratoLoteOut, status_code=201)
def create_lote(
    payload: ContratoLoteCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    cl = ContratoLote(**payload.model_dump())
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl


@lotes_router.get("/by-contrato/{contrato_id}", response_model=List[ContratoLoteOut])
def list_lotes(
    contrato_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    return db.query(ContratoLote).filter(ContratoLote.contrato_id == contrato_id).all()


# ─── Unidades de entrega ────────────────────────────────────────────────────

unidades_router = APIRouter(prefix="/unidades-entrega", tags=["contratos"])


@unidades_router.post("", response_model=UnidadEntregaOut, status_code=201)
def create_unidad(
    payload: UnidadEntregaCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    u = UnidadEntrega(**payload.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@unidades_router.get("/by-contrato/{contrato_id}", response_model=List[UnidadEntregaOut])
def list_unidades(
    contrato_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    return db.query(UnidadEntrega).filter(
        UnidadEntrega.contrato_id == contrato_id,
        UnidadEntrega.deleted_at.is_(None),
    ).order_by(UnidadEntrega.nombre).all()


@unidades_router.get("/{unidad_id}", response_model=UnidadEntregaOut)
def get_unidad(
    unidad_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    u = db.query(UnidadEntrega).filter(UnidadEntrega.id == unidad_id).first()
    if not u or u.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return u
