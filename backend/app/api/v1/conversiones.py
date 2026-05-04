"""Endpoints de conversiones producto catalogado <-> no-catalogado (Sprint 8)."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_db_session, require_tenant
from ...models import ConversionProducto, Producto
from ...schemas import ConversionCreate, ConversionUpdate, ConversionOut

router = APIRouter(prefix="/conversiones", tags=["conversiones"])


@router.get("", response_model=List[ConversionOut])
def list_conversiones(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
    catalogado_id: Optional[UUID] = Query(None),
    no_catalogado_id: Optional[UUID] = Query(None),
    activo: Optional[bool] = Query(None),
    limit: int = Query(200, le=2000),
    offset: int = Query(0, ge=0),
):
    q = db.query(ConversionProducto).filter(
        ConversionProducto.tenant_id == tenant_id
    )
    if catalogado_id:
        q = q.filter(ConversionProducto.producto_catalogado_id == catalogado_id)
    if no_catalogado_id:
        q = q.filter(ConversionProducto.producto_no_catalogado_id == no_catalogado_id)
    if activo is not None:
        q = q.filter(ConversionProducto.activo == activo)
    return q.order_by(
        ConversionProducto.prioridad,
        ConversionProducto.created_at.desc(),
    ).limit(limit).offset(offset).all()


@router.get("/{conv_id}", response_model=ConversionOut)
def get_conversion(
    conv_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    c = db.query(ConversionProducto).filter(
        ConversionProducto.id == conv_id,
        ConversionProducto.tenant_id == tenant_id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversion no encontrada")
    return c


@router.post("", status_code=201, response_model=ConversionOut)
def create_conversion(
    payload: ConversionCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    # Validar productos
    cat = db.query(Producto).filter(
        Producto.id == payload.producto_catalogado_id,
        Producto.tenant_id == tenant_id,
    ).first()
    no_cat = db.query(Producto).filter(
        Producto.id == payload.producto_no_catalogado_id,
        Producto.tenant_id == tenant_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Producto catalogado no existe")
    if not no_cat:
        raise HTTPException(status_code=404, detail="Producto no-catalogado no existe")
    if cat.id == no_cat.id:
        raise HTTPException(
            status_code=400,
            detail="catalogado y no-catalogado deben ser distintos productos",
        )

    # Si existe ya este par, error
    existing = db.query(ConversionProducto).filter(
        ConversionProducto.tenant_id == tenant_id,
        ConversionProducto.producto_catalogado_id == payload.producto_catalogado_id,
        ConversionProducto.producto_no_catalogado_id == payload.producto_no_catalogado_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe conversion {cat.nombre} <- {no_cat.nombre}",
        )

    conv = ConversionProducto(
        tenant_id=tenant_id,
        producto_catalogado_id=payload.producto_catalogado_id,
        producto_no_catalogado_id=payload.producto_no_catalogado_id,
        factor=payload.factor,
        merma_pct=payload.merma_pct,
        precio_no_cat=payload.precio_no_cat,
        mezcla_grupo_id=payload.mezcla_grupo_id,
        mezcla_proporcion=payload.mezcla_proporcion,
        prioridad=payload.prioridad,
        requiere_aprobacion=payload.requiere_aprobacion,
        activo=payload.activo,
        notas=payload.notas,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.patch("/{conv_id}", response_model=ConversionOut)
def update_conversion(
    conv_id: UUID,
    payload: ConversionUpdate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    conv = db.query(ConversionProducto).filter(
        ConversionProducto.id == conv_id,
        ConversionProducto.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversion no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(conv, field, value)
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/{conv_id}", status_code=204)
def delete_conversion(
    conv_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    conv = db.query(ConversionProducto).filter(
        ConversionProducto.id == conv_id,
        ConversionProducto.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversion no encontrada")
    db.delete(conv)
    db.commit()


@router.get("/producto/{producto_id}/conversiones-disponibles")
def conversiones_disponibles(
    producto_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Para un producto catalogado, lista los no-catalogados que pueden cubrirlo.

    Ordenado por prioridad. Usado en logica de sustitucion.
    """
    cat = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.tenant_id == tenant_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Producto no existe")

    convs = (
        db.query(ConversionProducto, Producto)
        .join(Producto, Producto.id == ConversionProducto.producto_no_catalogado_id)
        .filter(
            ConversionProducto.tenant_id == tenant_id,
            ConversionProducto.producto_catalogado_id == producto_id,
            ConversionProducto.activo.is_(True),
        )
        .order_by(ConversionProducto.prioridad)
        .all()
    )
    return [
        {
            "conversion_id": str(conv.id),
            "no_catalogado_id": str(prod.id),
            "no_catalogado_nombre": prod.nombre,
            "factor": float(conv.factor),
            "merma_pct": float(conv.merma_pct),
            "precio_no_cat": float(conv.precio_no_cat) if conv.precio_no_cat else None,
            "prioridad": conv.prioridad,
            "requiere_aprobacion": conv.requiere_aprobacion,
            "mezcla_grupo_id": str(conv.mezcla_grupo_id) if conv.mezcla_grupo_id else None,
        }
        for conv, prod in convs
    ]
