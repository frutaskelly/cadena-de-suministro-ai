"""Endpoints de ordenes de compra (Sprint 7)."""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from ..deps import get_db_session, require_tenant
from ...models import OrdenCompra, LineaOrdenCompra, Proveedor
from ...schemas import OrdenCompraCreate, OrdenCompraOut

router = APIRouter(prefix="/ordenes-compra", tags=["ordenes-compra"])


def _next_folio(db: Session, tenant_id: UUID) -> str:
    last = (
        db.query(OrdenCompra)
        .filter(OrdenCompra.tenant_id == tenant_id)
        .order_by(OrdenCompra.created_at.desc())
        .first()
    )
    if not last or not last.folio:
        return "OC-000001"
    try:
        n = int(last.folio.split("-")[-1])
        return f"OC-{n+1:06d}"
    except (ValueError, IndexError):
        c = db.query(func.count(OrdenCompra.id)).filter(
            OrdenCompra.tenant_id == tenant_id
        ).scalar() or 0
        return f"OC-{c+1:06d}"


@router.get("", response_model=List[OrdenCompraOut])
def list_ordenes(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
    estado: Optional[str] = Query(None),
    proveedor_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
):
    q = (
        db.query(OrdenCompra)
        .options(selectinload(OrdenCompra.lineas))
        .filter(OrdenCompra.tenant_id == tenant_id)
    )
    if estado:
        q = q.filter(OrdenCompra.estado == estado)
    if proveedor_id:
        q = q.filter(OrdenCompra.proveedor_id == proveedor_id)
    if fecha_desde:
        q = q.filter(OrdenCompra.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(OrdenCompra.fecha <= fecha_hasta)
    return q.order_by(OrdenCompra.created_at.desc()).limit(limit).offset(offset).all()


@router.get("/{orden_id}", response_model=OrdenCompraOut)
def get_orden(
    orden_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    oc = (
        db.query(OrdenCompra)
        .options(selectinload(OrdenCompra.lineas))
        .filter(OrdenCompra.id == orden_id, OrdenCompra.tenant_id == tenant_id)
        .first()
    )
    if not oc:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    return oc


@router.post("", status_code=201, response_model=OrdenCompraOut)
def create_orden(
    payload: OrdenCompraCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    # validar proveedor
    prov = db.query(Proveedor).filter(
        Proveedor.id == payload.proveedor_id,
        Proveedor.tenant_id == tenant_id,
    ).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no existe en este tenant")

    folio = payload.folio or _next_folio(db, tenant_id)
    oc = OrdenCompra(
        tenant_id=tenant_id,
        folio=folio,
        proveedor_id=payload.proveedor_id,
        pedido_origen_id=payload.pedido_origen_id,
        almacen_destino_id=payload.almacen_destino_id,
        fecha=payload.fecha,
        fecha_entrega_esperada=payload.fecha_entrega_esperada,
        estado=payload.estado,
        notas=payload.notas,
    )
    subtotal = Decimal(0)
    for ln in payload.lineas:
        lo = LineaOrdenCompra(
            tenant_id=tenant_id,
            producto_id=ln.producto_id,
            cantidad_solicitada=ln.cantidad_solicitada,
            presentacion=ln.presentacion,
            precio_unitario=ln.precio_unitario,
            importe=ln.importe,
            notas=ln.notas,
        )
        oc.lineas.append(lo)
        subtotal += ln.importe
    oc.subtotal = subtotal
    oc.iva_total = subtotal * Decimal("0.0")
    oc.total_estimado = subtotal
    db.add(oc)
    db.commit()
    db.refresh(oc)
    return oc


@router.post("/{orden_id}/transition")
def transition_oc(
    orden_id: UUID,
    nuevo_estado: str = Body(..., embed=True),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    valid = {
        "BORRADOR": ["ENVIADA", "CANCELADA"],
        "ENVIADA": ["ACEPTADA", "CANCELADA"],
        "ACEPTADA": ["EN_TRANSITO", "CANCELADA"],
        "EN_TRANSITO": ["RECIBIDA_PARCIAL", "RECIBIDA", "CANCELADA"],
        "RECIBIDA_PARCIAL": ["RECIBIDA", "CANCELADA"],
        "RECIBIDA": [],
        "CANCELADA": [],
    }
    oc = db.query(OrdenCompra).filter(
        OrdenCompra.id == orden_id,
        OrdenCompra.tenant_id == tenant_id,
    ).first()
    if not oc:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if nuevo_estado not in valid.get(oc.estado, []):
        raise HTTPException(
            status_code=400,
            detail=f"Transicion invalida {oc.estado} -> {nuevo_estado}",
        )
    oc.estado = nuevo_estado
    if nuevo_estado in ("RECIBIDA", "RECIBIDA_PARCIAL"):
        oc.fecha_recibida = date.today()
    db.commit()
    db.refresh(oc)
    return {"id": str(oc.id), "folio": oc.folio, "estado": oc.estado}
