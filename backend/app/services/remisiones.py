"""Servicio de remisiones: pedido -> remision -> factura.

Implementa el flujo del inventario triple-estado:
- generate_remision_from_pedido(): crea remision a partir de pedido (mueve disponible -> reservada)
- confirm_remision(): cliente confirma entrega, no afecta stock todavia
- factura_remision(): genera factura desde remision (mueve reservada -> facturada/sale)
- cancel_remision(): cancela y devuelve reservada -> disponible
- adjust_linea(): ajusta cantidad/precio/sustitucion en sitio
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from ..models import (
    Pedido, LineaPedido, Producto,
    Remision, LineaRemision, AjusteRemision,
    LoteInventario, MovimientoInventario, Almacen,
)


class RemisionError(Exception):
    pass


@dataclass
class RemisionGenerated:
    remision_id: UUID
    folio: str
    pedido_id: Optional[UUID]
    lineas_count: int
    total: Decimal
    warnings: list[str]


def _next_folio_remision(db: Session, tenant_id: UUID) -> str:
    """Genera folio incremental tipo R-000001."""
    last = (
        db.query(Remision)
        .filter(Remision.tenant_id == tenant_id)
        .order_by(Remision.created_at.desc())
        .first()
    )
    if not last:
        return "R-000001"
    try:
        # asume formato "R-NNNNNN"
        n = int(last.folio.split("-")[-1])
        return f"R-{n+1:06d}"
    except (ValueError, IndexError):
        # folio no numerico, fallback con count
        c = db.query(func.count(Remision.id)).filter(Remision.tenant_id == tenant_id).scalar() or 0
        return f"R-{c+1:06d}"


def generate_remision_from_pedido(
    db: Session,
    tenant_id: UUID,
    pedido_id: UUID,
    *,
    almacen_origen_id: Optional[UUID] = None,
    estado_inicial: str = "GENERADA",
    notas: Optional[str] = None,
) -> RemisionGenerated:
    """Crea una remision con sus lineas a partir de un pedido existente.

    No mueve inventario aun (eso pasa al EN_TRANSITO o ENTREGADA).
    """
    pedido: Pedido = (
        db.query(Pedido)
        .filter(Pedido.id == pedido_id, Pedido.tenant_id == tenant_id)
        .first()
    )
    if not pedido:
        raise RemisionError(f"Pedido {pedido_id} no existe")

    if pedido.estado in ("FACTURADO", "CANCELADO"):
        raise RemisionError(
            f"Pedido en estado '{pedido.estado}' no admite remision nueva"
        )

    # almacen default si no se especifica
    if not almacen_origen_id:
        default_alm = (
            db.query(Almacen)
            .filter(Almacen.tenant_id == tenant_id, Almacen.es_default.is_(True))
            .first()
        )
        if default_alm:
            almacen_origen_id = default_alm.id

    folio = _next_folio_remision(db, tenant_id)

    remision = Remision(
        tenant_id=tenant_id,
        folio=folio,
        pedido_id=pedido.id,
        cliente_id=pedido.cliente_facturacion_id,
        unidad_entrega_id=pedido.unidad_entrega_id,
        almacen_origen_id=almacen_origen_id,
        fecha_generada=date.today(),
        estado=estado_inicial,
        subtotal=pedido.subtotal,
        iva_total=pedido.iva,
        total=pedido.total,
        notas=notas,
        raw_payload={"source_pedido_folio": pedido.folio_interno},
    )
    db.add(remision)
    db.flush()  # get id

    warnings: list[str] = []
    lineas_count = 0
    for lp in pedido.lineas:
        if not lp.producto_id:
            warnings.append(
                f"linea {lp.numero_linea} sin producto -> excluida de remision"
            )
            continue
        lr = LineaRemision(
            tenant_id=tenant_id,
            remision_id=remision.id,
            linea_pedido_id=lp.id,
            producto_id=lp.producto_id,
            cantidad_solicitada=lp.cantidad_solicitada,
            cantidad_entregada=lp.cantidad_solicitada,  # default = lo pedido
            presentacion=lp.presentacion,
            precio_unitario=lp.precio_unitario,
            importe=lp.importe,
        )
        db.add(lr)
        lineas_count += 1

    db.commit()
    db.refresh(remision)

    return RemisionGenerated(
        remision_id=remision.id,
        folio=remision.folio,
        pedido_id=remision.pedido_id,
        lineas_count=lineas_count,
        total=remision.total or Decimal(0),
        warnings=warnings,
    )


def transition_remision(
    db: Session,
    tenant_id: UUID,
    remision_id: UUID,
    nuevo_estado: str,
    *,
    user_id: Optional[UUID] = None,
) -> Remision:
    """Transiciona el estado de una remision.

    Estados validos: GENERADA -> EN_TRANSITO -> ENTREGADA -> CONFIRMADA -> FACTURADA
                                                          -> CANCELADA (en cualquier momento)
    """
    valid_transitions = {
        "GENERADA": ["EN_TRANSITO", "CANCELADA"],
        "EN_TRANSITO": ["ENTREGADA", "CANCELADA"],
        "ENTREGADA": ["CONFIRMADA", "CANCELADA"],
        "CONFIRMADA": ["FACTURADA", "CANCELADA"],
        "FACTURADA": [],  # final
        "CANCELADA": [],  # final
    }
    rem: Remision = (
        db.query(Remision)
        .filter(Remision.id == remision_id, Remision.tenant_id == tenant_id)
        .first()
    )
    if not rem:
        raise RemisionError(f"Remision {remision_id} no existe")

    allowed = valid_transitions.get(rem.estado, [])
    if nuevo_estado not in allowed:
        raise RemisionError(
            f"Transicion invalida: {rem.estado} -> {nuevo_estado}. "
            f"Permitidas: {allowed}"
        )

    rem.estado = nuevo_estado
    if nuevo_estado == "ENTREGADA":
        rem.fecha_entrega = datetime.utcnow()
    if nuevo_estado == "FACTURADA":
        rem.fecha_facturada = datetime.utcnow()

    # Mover inventario al EN_TRANSITO (sale de almacen)
    if nuevo_estado == "EN_TRANSITO":
        _move_inventory_remision_out(db, tenant_id, rem)
    # Devolver al CANCELADA (vuelve a disponible)
    if nuevo_estado == "CANCELADA" and rem.estado != "GENERADA":
        # solo si ya habia salido (estado previo era EN_TRANSITO/ENTREGADA/CONFIRMADA)
        # se devuelve la reservada a disponible
        _move_inventory_remision_back(db, tenant_id, rem)

    db.commit()
    db.refresh(rem)
    return rem


def _move_inventory_remision_out(db: Session, tenant_id: UUID, rem: Remision) -> None:
    """Mueve cantidad de disponible -> reservada cuando remision sale del almacen."""
    for lr in rem.lineas if hasattr(rem, "lineas") else []:
        if not lr.lote_inventario_id:
            # no asignamos lote especifico todavia (sprint 7 simplificado)
            continue
        lote: LoteInventario = db.get(LoteInventario, lr.lote_inventario_id)
        if not lote:
            continue
        qty = lr.cantidad_entregada
        if lote.cantidad_disponible < qty:
            raise RemisionError(
                f"Lote {lote.id} sin stock suficiente: tiene {lote.cantidad_disponible}, "
                f"se requiere {qty}"
            )
        lote.cantidad_disponible -= qty
        lote.cantidad_reservada = (lote.cantidad_reservada or Decimal(0)) + qty

        mov = MovimientoInventario(
            tenant_id=tenant_id,
            tipo="SALIDA_REMISION",
            lote_id=lote.id,
            cantidad=-qty,
            costo_unitario=lote.costo_unitario,
            ref_tipo="REMISION",
            ref_id=rem.id,
            motivo=f"Remision {rem.folio} salida",
        )
        db.add(mov)


def _move_inventory_remision_back(db: Session, tenant_id: UUID, rem: Remision) -> None:
    """Devuelve reservada -> disponible cuando se cancela remision."""
    for lr in rem.lineas if hasattr(rem, "lineas") else []:
        if not lr.lote_inventario_id:
            continue
        lote: LoteInventario = db.get(LoteInventario, lr.lote_inventario_id)
        if not lote:
            continue
        qty = lr.cantidad_entregada
        lote.cantidad_disponible += qty
        lote.cantidad_reservada = max(
            (lote.cantidad_reservada or Decimal(0)) - qty, Decimal(0)
        )

        mov = MovimientoInventario(
            tenant_id=tenant_id,
            tipo="CANCELACION_REMISION",
            lote_id=lote.id,
            cantidad=qty,
            costo_unitario=lote.costo_unitario,
            ref_tipo="REMISION",
            ref_id=rem.id,
            motivo=f"Cancelacion remision {rem.folio}",
        )
        db.add(mov)


def adjust_linea_remision(
    db: Session,
    tenant_id: UUID,
    linea_id: UUID,
    *,
    nueva_cantidad: Optional[Decimal] = None,
    nuevo_precio: Optional[Decimal] = None,
    motivo: Optional[str] = None,
    user_id: Optional[UUID] = None,
) -> AjusteRemision:
    """Ajusta una linea de remision en sitio.

    Genera un AjusteRemision append-only y actualiza la linea.
    """
    lr: LineaRemision = (
        db.query(LineaRemision)
        .filter(LineaRemision.id == linea_id, LineaRemision.tenant_id == tenant_id)
        .first()
    )
    if not lr:
        raise RemisionError(f"Linea remision {linea_id} no existe")

    rem: Remision = lr.remision_id  # type: ignore[assignment]
    rem_obj = db.get(Remision, lr.remision_id)
    if not rem_obj or rem_obj.estado in ("FACTURADA", "CANCELADA"):
        raise RemisionError(
            f"Remision {lr.remision_id} no admite ajustes en estado actual"
        )

    tipo = "PESO" if nueva_cantidad is not None else "PRECIO"
    ajuste = AjusteRemision(
        tenant_id=tenant_id,
        remision_id=lr.remision_id,
        linea_remision_id=lr.id,
        tipo=tipo,
        cantidad_anterior=lr.cantidad_entregada if nueva_cantidad is not None else None,
        cantidad_nueva=nueva_cantidad,
        precio_anterior=lr.precio_unitario if nuevo_precio is not None else None,
        precio_nuevo=nuevo_precio,
        motivo=motivo,
        created_by=user_id,
    )
    db.add(ajuste)

    if nueva_cantidad is not None:
        lr.cantidad_entregada = nueva_cantidad
        lr.importe = nueva_cantidad * lr.precio_unitario
        lr.motivo_ajuste = motivo
    if nuevo_precio is not None:
        lr.precio_unitario = nuevo_precio
        lr.importe = lr.cantidad_entregada * nuevo_precio

    db.commit()
    db.refresh(ajuste)
    return ajuste


def get_inventario_triple_estado(
    db: Session,
    tenant_id: UUID,
    *,
    almacen_id: Optional[UUID] = None,
) -> list[dict]:
    """Snapshot del inventario triple-estado por producto/almacen.

    Retorna lista de dicts con:
    - producto_id, producto_nombre, almacen_id
    - cantidad_fisica (sum lotes.cantidad_disponible)
    - cantidad_remision (sum lotes.cantidad_reservada)
    - cantidad_facturada_acumulada (sum lineas_remision con cantidad_facturada NOT NULL)
    """
    q = (
        db.query(
            LoteInventario.producto_id.label("producto_id"),
            LoteInventario.almacen_id.label("almacen_id"),
            Producto.nombre.label("producto_nombre"),
            func.coalesce(func.sum(LoteInventario.cantidad_disponible), 0).label("cantidad_fisica"),
            func.coalesce(func.sum(LoteInventario.cantidad_reservada), 0).label("cantidad_remision"),
        )
        .join(Producto, Producto.id == LoteInventario.producto_id)
        .filter(LoteInventario.tenant_id == tenant_id)
        .group_by(
            LoteInventario.producto_id,
            LoteInventario.almacen_id,
            Producto.nombre,
        )
    )
    if almacen_id:
        q = q.filter(LoteInventario.almacen_id == almacen_id)

    out = []
    for r in q.all():
        # facturado acumulado = sum(cantidad_facturada) por producto
        facturado = (
            db.query(func.coalesce(func.sum(LineaRemision.cantidad_facturada), 0))
            .filter(
                LineaRemision.tenant_id == tenant_id,
                LineaRemision.producto_id == r.producto_id,
                LineaRemision.cantidad_facturada.isnot(None),
            )
            .scalar()
            or Decimal(0)
        )
        fisica = Decimal(r.cantidad_fisica)
        remision = Decimal(r.cantidad_remision)
        out.append({
            "producto_id": str(r.producto_id),
            "producto_nombre": r.producto_nombre,
            "almacen_id": str(r.almacen_id),
            "cantidad_fisica": fisica,
            "cantidad_remision": remision,
            "cantidad_facturada_acumulada": facturado,
            "total_disponible_efectivo": fisica - remision,
        })
    return out
