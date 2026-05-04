"""Endpoints de dashboard para operación diaria."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from ..deps import get_db_session, require_tenant
from ...models import (
    Pedido, LineaPedido, Producto, Cliente, UnidadEntrega, Contrato,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/resumen-dia")
def resumen_dia(
    fecha: Optional[date] = Query(None, description="Single day (legacy). Si presente, ignora desde/hasta."),
    desde: Optional[date] = Query(None, description="Inicio del rango (inclusive)"),
    hasta: Optional[date] = Query(None, description="Fin del rango (inclusive)"),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Metricas agregadas del rango (default: este mes hasta hoy).

    - Si `fecha` se pasa: agrega solo ese dia (legacy).
    - Si `desde`/`hasta` se pasan: agrega rango.
    - Sin args: del primer dia del mes actual a hoy.
    """
    today = date.today()
    if fecha:
        desde = hasta = fecha
    else:
        desde = desde or today.replace(day=1)
        hasta = hasta or today

    base = db.query(Pedido).filter(
        Pedido.tenant_id == tenant_id,
        Pedido.fecha_pedido >= desde,
        Pedido.fecha_pedido <= hasta,
        Pedido.deleted_at.is_(None),
    )
    pedidos = base.all()

    n_pedidos = len(pedidos)
    n_review = sum(1 for p in pedidos if p.requires_review)
    total_dia = sum((p.total or Decimal("0")) for p in pedidos)
    por_estado: dict[str, int] = {}
    por_canal: dict[str, int] = {}
    for p in pedidos:
        por_estado[p.estado] = por_estado.get(p.estado, 0) + 1
        por_canal[p.canal] = por_canal.get(p.canal, 0) + 1

    n_lineas = db.query(func.count(LineaPedido.id)).join(
        Pedido, Pedido.id == LineaPedido.pedido_id,
    ).filter(
        Pedido.tenant_id == tenant_id,
        Pedido.fecha_pedido >= desde,
        Pedido.fecha_pedido <= hasta,
    ).scalar() or 0

    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "fecha": (desde.isoformat() if desde == hasta else None),  # legacy single-day
        "pedidos_count": n_pedidos,
        "pedidos_requires_review": n_review,
        "lineas_count": int(n_lineas),
        "total_dia": float(total_dia),
        "por_estado": por_estado,
        "por_canal": por_canal,
    }


@router.get("/top-productos")
def top_productos(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Top productos por volumen y revenue en el rango."""
    today = date.today()
    desde = desde or (today - timedelta(days=30))
    hasta = hasta or today

    rows = db.query(
        Producto.id,
        Producto.sku_interno,
        Producto.nombre,
        func.sum(LineaPedido.cantidad_solicitada).label("cantidad"),
        func.sum(LineaPedido.importe).label("importe"),
        func.count(LineaPedido.id).label("apariciones"),
    ).join(
        LineaPedido, LineaPedido.producto_id == Producto.id,
    ).join(
        Pedido, Pedido.id == LineaPedido.pedido_id,
    ).filter(
        Pedido.tenant_id == tenant_id,
        Pedido.fecha_pedido >= desde,
        Pedido.fecha_pedido <= hasta,
        Pedido.deleted_at.is_(None),
    ).group_by(
        Producto.id, Producto.sku_interno, Producto.nombre,
    ).order_by(desc("importe")).limit(limit).all()

    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "items": [
            {
                "producto_id": str(r.id),
                "sku": r.sku_interno,
                "nombre": r.nombre,
                "cantidad_total": float(r.cantidad or 0),
                "importe_total": float(r.importe or 0),
                "apariciones": int(r.apariciones or 0),
            }
            for r in rows
        ],
    }


@router.get("/top-unidades")
def top_unidades(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    today = date.today()
    desde = desde or (today - timedelta(days=30))
    hasta = hasta or today

    rows = db.query(
        UnidadEntrega.id,
        UnidadEntrega.nombre,
        UnidadEntrega.tipo,
        func.count(Pedido.id).label("pedidos"),
        func.sum(Pedido.total).label("total"),
    ).join(
        Pedido, Pedido.unidad_entrega_id == UnidadEntrega.id,
    ).filter(
        Pedido.tenant_id == tenant_id,
        Pedido.fecha_pedido >= desde,
        Pedido.fecha_pedido <= hasta,
        Pedido.deleted_at.is_(None),
    ).group_by(
        UnidadEntrega.id, UnidadEntrega.nombre, UnidadEntrega.tipo,
    ).order_by(desc("total")).limit(limit).all()

    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "items": [
            {
                "unidad_id": str(r.id),
                "nombre": r.nombre,
                "tipo": r.tipo,
                "pedidos_count": int(r.pedidos or 0),
                "total_revenue": float(r.total or 0),
            }
            for r in rows
        ],
    }


@router.get("/lineas-sin-producto")
def lineas_sin_producto(
    desde: Optional[date] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Líneas de pedido cuyo `producto_id` no se resolvió.

    Útil para identificar productos del agente que faltan en catálogo.
    """
    desde = desde or (date.today() - timedelta(days=30))
    rows = db.query(
        LineaPedido.id,
        LineaPedido.texto_original,
        LineaPedido.cantidad_solicitada,
        Pedido.fecha_pedido,
        UnidadEntrega.nombre.label("unidad_nombre"),
    ).join(
        Pedido, Pedido.id == LineaPedido.pedido_id,
    ).join(
        UnidadEntrega, UnidadEntrega.id == Pedido.unidad_entrega_id,
    ).filter(
        Pedido.tenant_id == tenant_id,
        LineaPedido.producto_id.is_(None),
        Pedido.fecha_pedido >= desde,
    ).order_by(desc(Pedido.fecha_pedido)).limit(limit).all()

    return {
        "desde": desde.isoformat(),
        "items": [
            {
                "linea_id": str(r.id),
                "texto_original": r.texto_original,
                "cantidad": float(r.cantidad_solicitada or 0),
                "fecha": r.fecha_pedido.isoformat() if r.fecha_pedido else None,
                "unidad": r.unidad_nombre,
            }
            for r in rows
        ],
    }
