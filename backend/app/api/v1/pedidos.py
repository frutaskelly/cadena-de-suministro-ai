from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from ..deps import get_db_session, require_tenant
from ...models import Pedido, LineaPedido
from ...schemas import PedidoCreate, PedidoOut
from ...services.pedidos import from_batch_rows, PedidoRowIn

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


class FromBatchRowIn(BaseModel):
    unidad_nombre: str
    alimento: str
    cantidad: Decimal
    presentacion: str = "KILO"
    lote: Optional[str] = None
    cba: Optional[str] = None


class FromBatchIn(BaseModel):
    fecha: date
    canal: str = Field("EXCEL_BD", description="EXCEL_BD | LIBRETA_FOTO | VOZ | WEB | API")
    contrato_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None
    rows: list[FromBatchRowIn]
    force_overwrite: bool = False
    raw_payload: Optional[dict] = None
    fuzzy_threshold: float = 80.0


@router.post("/from-batch", status_code=201)
def create_pedidos_from_batch(
    payload: FromBatchIn,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Crea pedidos desde un batch de rows (Excel BD, libreta, voz, etc.).

    Agrupa rows por `unidad_nombre`, resuelve unidad/producto con fuzzy match,
    calcula precios desde la lista del cliente y crea 1 Pedido por unidad.
    """
    rows = [PedidoRowIn(**r.model_dump()) for r in payload.rows]
    result = from_batch_rows(
        db=db,
        tenant_id=tenant_id,
        fecha=payload.fecha,
        rows=rows,
        canal=payload.canal,
        contrato_id=payload.contrato_id,
        cliente_id=payload.cliente_id,
        force_overwrite=payload.force_overwrite,
        raw_payload=payload.raw_payload,
        fuzzy_threshold=payload.fuzzy_threshold,
    )
    return {
        "fecha": result.fecha.isoformat(),
        "pedidos_creados": [
            {
                "pedido_id": str(p.pedido_id),
                "folio_interno": p.folio_interno,
                "unidad_nombre": p.unidad_nombre,
                "lineas_count": p.lineas_count,
                "total": float(p.total),
                "requires_review": p.requires_review,
            }
            for p in result.pedidos_creados
        ],
        "pedidos_skipped": result.pedidos_skipped,
        "unidades_sin_match": result.unidades_sin_match,
        "lineas_sin_match": result.lineas_sin_match,
        "warnings": result.warnings,
    }


@router.post("/from-excel-bd", status_code=201)
def create_pedidos_from_excel_bd(
    payload: FromBatchIn,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Alias específico para EHMO Excel BD. Forza canal=EXCEL_BD."""
    payload.canal = "EXCEL_BD"
    return create_pedidos_from_batch(payload, db, tenant_id)


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
