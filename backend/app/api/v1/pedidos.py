from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from ..deps import get_db_session, require_tenant
from ...models import Pedido, LineaPedido
from ...schemas import PedidoCreate, PedidoOut

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("", response_model=PedidoOut, status_code=201)
def create_pedido(
    payload: PedidoCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    data = payload.model_dump(exclude={"lineas"})
    p = Pedido(**data, tenant_id=tenant_id)
    db.add(p)
    db.flush()  # genera p.id

    subtotal = Decimal("0")
    for linea in payload.lineas:
        l = LineaPedido(**linea.model_dump(), pedido_id=p.id)
        db.add(l)
        subtotal += linea.importe
    p.subtotal = subtotal
    p.total = subtotal  # IVA se calcula al facturar (FyV exenta)

    db.commit()
    db.refresh(p)
    return p


@router.get("", response_model=List[PedidoOut])
def list_pedidos(
    fecha: Optional[date] = Query(None, description="Filtrar por fecha"),
    estado: Optional[str] = None,
    cliente_id: Optional[UUID] = None,
    requires_review: Optional[bool] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    query = db.query(Pedido).filter(
        Pedido.tenant_id == tenant_id,
        Pedido.deleted_at.is_(None),
    ).options(selectinload(Pedido.lineas))
    if fecha:
        query = query.filter(Pedido.fecha_pedido == fecha)
    if estado:
        query = query.filter(Pedido.estado == estado)
    if cliente_id:
        query = query.filter(Pedido.cliente_facturacion_id == cliente_id)
    if requires_review is not None:
        query = query.filter(Pedido.requires_review == requires_review)
    return query.order_by(Pedido.fecha_pedido.desc()).offset(offset).limit(limit).all()


@router.get("/{pedido_id}", response_model=PedidoOut)
def get_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    p = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant_id,
    ).options(selectinload(Pedido.lineas)).first()
    if not p or p.deleted_at:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return p
