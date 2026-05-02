"""Endpoints read-only de catálogos SAT.

Sin tenant_id (catálogos globales). No requiere x-tenant-id.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_db_session
from ...models import (
    SatFormaPago, SatMetodoPago, SatRegimenFiscal, SatUsoCfdi,
    SatUnidad, SatProductoServicio,
)

router = APIRouter(prefix="/sat", tags=["sat-catalogos"])


@router.get("/formas-pago")
def list_formas_pago(db: Session = Depends(get_db_session)):
    rows = db.query(SatFormaPago).order_by(SatFormaPago.clave).all()
    return [{"clave": r.clave, "descripcion": r.descripcion} for r in rows]


@router.get("/metodos-pago")
def list_metodos_pago(db: Session = Depends(get_db_session)):
    rows = db.query(SatMetodoPago).order_by(SatMetodoPago.clave).all()
    return [{"clave": r.clave, "descripcion": r.descripcion} for r in rows]


@router.get("/regimenes")
def list_regimenes(
    aplica: Optional[str] = Query(None, regex="^(fisica|moral)$"),
    db: Session = Depends(get_db_session),
):
    q = db.query(SatRegimenFiscal)
    if aplica == "fisica":
        q = q.filter(SatRegimenFiscal.aplica_fisica == "Sí")
    elif aplica == "moral":
        q = q.filter(SatRegimenFiscal.aplica_moral == "Sí")
    rows = q.order_by(SatRegimenFiscal.clave).all()
    return [
        {
            "clave": r.clave,
            "descripcion": r.descripcion,
            "aplica_fisica": r.aplica_fisica,
            "aplica_moral": r.aplica_moral,
        }
        for r in rows
    ]


@router.get("/usos-cfdi")
def list_usos_cfdi(
    aplica: Optional[str] = Query(None, regex="^(fisica|moral)$"),
    db: Session = Depends(get_db_session),
):
    q = db.query(SatUsoCfdi)
    if aplica == "fisica":
        q = q.filter(SatUsoCfdi.aplica_fisica == "Sí")
    elif aplica == "moral":
        q = q.filter(SatUsoCfdi.aplica_moral == "Sí")
    rows = q.order_by(SatUsoCfdi.clave).all()
    return [
        {
            "clave": r.clave,
            "descripcion": r.descripcion,
            "aplica_fisica": r.aplica_fisica,
            "aplica_moral": r.aplica_moral,
        }
        for r in rows
    ]


@router.get("/unidades")
def list_unidades(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db_session),
):
    query = db.query(SatUnidad)
    if q:
        like = f"%{q.lower()}%"
        from sqlalchemy import or_, func
        query = query.filter(or_(
            func.lower(SatUnidad.clave).like(like),
            func.lower(SatUnidad.nombre).like(like),
        ))
    rows = query.order_by(SatUnidad.clave).limit(200).all()
    return [
        {
            "clave": r.clave,
            "nombre": r.nombre,
            "descripcion": r.descripcion,
            "simbolo": r.simbolo,
        }
        for r in rows
    ]


@router.get("/productos-servicios")
def list_productos_servicios(
    q: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db_session),
):
    query = db.query(SatProductoServicio)
    if q:
        from sqlalchemy import or_, func
        like = f"%{q.lower()}%"
        query = query.filter(or_(
            SatProductoServicio.clave.like(f"%{q}%"),
            func.lower(SatProductoServicio.descripcion).like(like),
        ))
    rows = query.order_by(SatProductoServicio.clave).limit(limit).all()
    return [
        {
            "clave": r.clave,
            "descripcion": r.descripcion,
            "categoria": r.categoria,
        }
        for r in rows
    ]
