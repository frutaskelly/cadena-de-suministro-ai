from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from ..deps import get_db_session, require_tenant
from ...models import Cliente
from ...schemas import ClienteCreate, ClienteOut, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClienteOut, status_code=201)
def create_cliente(
    payload: ClienteCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    if payload.codigo:
        existing = db.query(Cliente).filter(
            Cliente.tenant_id == tenant_id,
            Cliente.codigo == payload.codigo,
            Cliente.deleted_at.is_(None),
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"código '{payload.codigo}' ya existe")
    c = Cliente(**payload.model_dump(), tenant_id=tenant_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("", response_model=List[ClienteOut])
def list_clientes(
    q: Optional[str] = Query(None, description="Búsqueda por nombre o RFC"),
    tipo: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    query = db.query(Cliente).filter(
        Cliente.tenant_id == tenant_id,
        Cliente.deleted_at.is_(None),
    )
    if tipo:
        query = query.filter(Cliente.tipo == tipo)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(
            func.lower(Cliente.legal_name).like(like),
            func.lower(Cliente.rfc).like(like),
            func.lower(Cliente.codigo).like(like),
        ))
    return query.order_by(Cliente.legal_name).offset(offset).limit(limit).all()


@router.get("/{cliente_id}", response_model=ClienteOut)
def get_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    c = db.query(Cliente).filter(
        Cliente.id == cliente_id,
        Cliente.tenant_id == tenant_id,
        Cliente.deleted_at.is_(None),
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return c


@router.patch("/{cliente_id}", response_model=ClienteOut)
def update_cliente(
    cliente_id: UUID,
    payload: ClienteUpdate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    c = db.query(Cliente).filter(
        Cliente.id == cliente_id,
        Cliente.tenant_id == tenant_id,
        Cliente.deleted_at.is_(None),
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{cliente_id}", status_code=204)
def delete_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    from datetime import datetime, timezone
    c = db.query(Cliente).filter(
        Cliente.id == cliente_id,
        Cliente.tenant_id == tenant_id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    c.deleted_at = datetime.now(timezone.utc)
    db.commit()
