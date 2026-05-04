"""Endpoints de remisiones (Sprint 7)."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from ..deps import get_db_session, require_tenant
from ...models import Remision, LineaRemision, AjusteRemision, Pedido
from ...schemas import (
    RemisionCreate, RemisionOut,
    AjusteRemisionCreate, AjusteRemisionOut,
)
from ...services.remisiones import (
    generate_remision_from_pedido,
    transition_remision,
    adjust_linea_remision,
    get_inventario_triple_estado,
    RemisionError,
    _next_folio_remision,
)

router = APIRouter(prefix="/remisiones", tags=["remisiones"])


@router.get("", response_model=List[RemisionOut])
def list_remisiones(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
    estado: Optional[str] = Query(None),
    cliente_id: Optional[UUID] = Query(None),
    pedido_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
):
    q = (
        db.query(Remision)
        .options(selectinload(Remision.lineas))
        .filter(Remision.tenant_id == tenant_id)
    )
    if estado:
        q = q.filter(Remision.estado == estado)
    if cliente_id:
        q = q.filter(Remision.cliente_id == cliente_id)
    if pedido_id:
        q = q.filter(Remision.pedido_id == pedido_id)
    if fecha_desde:
        q = q.filter(Remision.fecha_generada >= fecha_desde)
    if fecha_hasta:
        q = q.filter(Remision.fecha_generada <= fecha_hasta)
    return q.order_by(Remision.created_at.desc()).limit(limit).offset(offset).all()


@router.get("/{remision_id}", response_model=RemisionOut)
def get_remision(
    remision_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    rem = (
        db.query(Remision)
        .options(selectinload(Remision.lineas))
        .filter(Remision.id == remision_id, Remision.tenant_id == tenant_id)
        .first()
    )
    if not rem:
        raise HTTPException(status_code=404, detail="Remision no encontrada")
    return rem


@router.post("", status_code=201, response_model=RemisionOut)
def create_remision(
    payload: RemisionCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Crea remision manual con sus lineas."""
    folio = payload.folio or _next_folio_remision(db, tenant_id)
    rem = Remision(
        tenant_id=tenant_id,
        folio=folio,
        pedido_id=payload.pedido_id,
        cliente_id=payload.cliente_id,
        unidad_entrega_id=payload.unidad_entrega_id,
        almacen_origen_id=payload.almacen_origen_id,
        fecha_generada=payload.fecha_generada or date.today(),
        estado=payload.estado,
        notas=payload.notas,
        raw_payload=payload.raw_payload,
    )
    subtotal = Decimal(0)
    for ln in payload.lineas:
        lr = LineaRemision(
            tenant_id=tenant_id,
            producto_id=ln.producto_id,
            linea_pedido_id=ln.linea_pedido_id,
            lote_inventario_id=ln.lote_inventario_id,
            cantidad_solicitada=ln.cantidad_solicitada,
            cantidad_entregada=ln.cantidad_entregada,
            presentacion=ln.presentacion,
            precio_unitario=ln.precio_unitario,
            importe=ln.importe,
            motivo_ajuste=ln.motivo_ajuste,
        )
        rem.lineas.append(lr)
        subtotal += ln.importe
    rem.subtotal = subtotal
    rem.iva_total = subtotal * Decimal("0.0")  # IVA 0 para alimentos basicos por default
    rem.total = subtotal
    db.add(rem)
    db.commit()
    db.refresh(rem)
    return rem


@router.post("/from-pedido/{pedido_id}", status_code=201)
def create_remision_from_pedido(
    pedido_id: UUID,
    almacen_origen_id: Optional[UUID] = Body(None),
    notas: Optional[str] = Body(None),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Crea remision desde un pedido existente con todas sus lineas."""
    try:
        result = generate_remision_from_pedido(
            db=db,
            tenant_id=tenant_id,
            pedido_id=pedido_id,
            almacen_origen_id=almacen_origen_id,
            notas=notas,
        )
    except RemisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "remision_id": str(result.remision_id),
        "folio": result.folio,
        "pedido_id": str(result.pedido_id) if result.pedido_id else None,
        "lineas_count": result.lineas_count,
        "total": float(result.total),
        "warnings": result.warnings,
    }


class TransitionPayload(BaseModel):
    nuevo_estado: str


@router.post("/{remision_id}/transition", response_model=RemisionOut)
def transition_remision_endpoint(
    remision_id: UUID,
    payload: TransitionPayload,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Transiciona el estado de una remision."""
    try:
        rem = transition_remision(
            db=db, tenant_id=tenant_id, remision_id=remision_id,
            nuevo_estado=payload.nuevo_estado,
        )
    except RemisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(rem)
    return rem


class AjusteLineaPayload(BaseModel):
    nueva_cantidad: Optional[Decimal] = None
    nuevo_precio: Optional[Decimal] = None
    motivo: Optional[str] = None


@router.post("/lineas/{linea_id}/ajustar", response_model=AjusteRemisionOut)
def ajustar_linea(
    linea_id: UUID,
    payload: AjusteLineaPayload,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Ajusta cantidad o precio de una linea de remision in situ."""
    if payload.nueva_cantidad is None and payload.nuevo_precio is None:
        raise HTTPException(
            status_code=400,
            detail="Debe enviar nueva_cantidad y/o nuevo_precio",
        )
    try:
        ajuste = adjust_linea_remision(
            db=db, tenant_id=tenant_id, linea_id=linea_id,
            nueva_cantidad=payload.nueva_cantidad,
            nuevo_precio=payload.nuevo_precio,
            motivo=payload.motivo,
        )
    except RemisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ajuste


@router.get("/inventario/triple-estado")
def inventario_triple_estado(
    almacen_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Retorna inventario en sus 3 estados (fisico/remision/facturado) por producto."""
    return get_inventario_triple_estado(
        db=db, tenant_id=tenant_id, almacen_id=almacen_id,
    )
