"""Lógica de creación de pedidos desde formatos heredados.

Sirve para:
- Excel BD que manda EHMO (legado: hoja "BD" con UNIDAD, LOTE, CBA, ALIMENTO,
  PRESENTACION, CANTIDAD)
- Libreta foto/voz de SUREÑA
- Cualquier batch de rows pre-parseadas

El agente legacy (Whatsapp_agent) puede mandar el JSON directo a este endpoint
en lugar de seguir generando archivos JSON locales.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import (
    Cliente, Contrato, ContratoLote, UnidadEntrega,
    Producto, Precio, ListaPrecios, Pedido, LineaPedido,
)
from .fuzzy_match import best_match, normalize


@dataclass
class PedidoRowIn:
    unidad_nombre: str
    alimento: str
    cantidad: Decimal
    presentacion: str = "KILO"
    lote: Optional[str] = None
    cba: Optional[str] = None


@dataclass
class PedidoLineaResolved:
    numero_linea: int
    producto_id: Optional[UUID]
    producto_nombre: Optional[str]
    presentacion: str
    cantidad_solicitada: Decimal
    precio_unitario: Decimal
    importe: Decimal
    texto_original: str
    match_confidence: Optional[float]
    needs_review: bool = False


@dataclass
class PedidoBuilt:
    pedido_id: UUID
    folio_interno: Optional[str]
    unidad_entrega_id: UUID
    unidad_nombre: str
    cliente_id: UUID
    fecha: date
    total: Decimal
    lineas_count: int
    requires_review: bool


@dataclass
class FromBatchResult:
    fecha: date
    pedidos_creados: list[PedidoBuilt] = field(default_factory=list)
    pedidos_skipped: list[dict] = field(default_factory=list)
    unidades_sin_match: list[str] = field(default_factory=list)
    lineas_sin_match: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _resolve_producto(
    db: Session, tenant_id: UUID, alimento: str,
) -> Optional[Producto]:
    """Resuelve producto por nombre/sinónimos. Devuelve None si no matchea."""
    norm = normalize(alimento)
    if not norm:
        return None

    productos = db.query(Producto).filter(
        Producto.tenant_id == tenant_id,
        Producto.deleted_at.is_(None),
        Producto.activo.is_(True),
    ).all()

    # 1. Sinónimos exactos
    for p in productos:
        if p.sinonimos:
            for s in p.sinonimos:
                if normalize(s) == norm:
                    return p

    # 2. Containment bidirecccional sobre nombre normalizado
    for p in productos:
        n = normalize(p.nombre)
        if n == norm:
            return p
    for p in productos:
        n = normalize(p.nombre)
        if n in norm or norm in n:
            return p

    # 3. Sinónimos containment
    for p in productos:
        if p.sinonimos:
            for s in p.sinonimos:
                ns = normalize(s)
                if ns and (ns in norm or norm in ns):
                    return p

    return None


def _resolve_precio(
    db: Session, lista_id: UUID, producto_id: UUID, presentacion: str,
) -> Optional[Decimal]:
    p = db.query(Precio).filter(
        Precio.lista_id == lista_id,
        Precio.producto_id == producto_id,
        Precio.presentacion == presentacion,
    ).first()
    if p:
        return p.precio_unitario
    # Fallback: ignorar presentación
    p = db.query(Precio).filter(
        Precio.lista_id == lista_id,
        Precio.producto_id == producto_id,
    ).first()
    return p.precio_unitario if p else None


def from_batch_rows(
    db: Session,
    tenant_id: UUID,
    fecha: date,
    rows: list[PedidoRowIn],
    canal: str = "EXCEL_BD",
    contrato_id: Optional[UUID] = None,
    cliente_id: Optional[UUID] = None,
    force_overwrite: bool = False,
    raw_payload: Optional[dict] = None,
    fuzzy_threshold: float = 80.0,
) -> FromBatchResult:
    """Crea pedidos a partir de rows (UNIDAD, ALIMENTO, CANTIDAD, ...).

    Reglas:
    - Agrupa rows por unidad_nombre → 1 pedido por unidad
    - Resuelve unidad con fuzzy matching contra UnidadEntrega del contrato
    - Resuelve producto con sinónimos + containment
    - Si force_overwrite=False y ya existe pedido (fecha, unidad), lo skip
    """
    res = FromBatchResult(fecha=fecha)

    # Resolver contrato + cliente + lista de precios
    if contrato_id:
        contrato = db.query(Contrato).filter(
            Contrato.id == contrato_id, Contrato.tenant_id == tenant_id,
        ).first()
    else:
        # Default: contrato EHMO si canal=EXCEL_BD, SUREÑA si LIBRETA_FOTO/VOZ
        contratante = "EHMO" if canal == "EXCEL_BD" else "SUREÑA"
        contrato = db.query(Contrato).filter(
            Contrato.tenant_id == tenant_id,
            Contrato.contratante == contratante,
        ).first()

    if not contrato:
        res.warnings.append(f"No se encontró contrato (canal={canal})")
        return res

    lote = db.query(ContratoLote).filter(
        ContratoLote.contrato_id == contrato.id,
    ).first()

    # Cliente: si no se especifica, busca uno asociado al contratante
    if cliente_id:
        cliente = db.query(Cliente).filter(
            Cliente.id == cliente_id, Cliente.tenant_id == tenant_id,
        ).first()
    else:
        codigo_default = "EHMO" if canal == "EXCEL_BD" else "SURENA"
        cliente = db.query(Cliente).filter(
            Cliente.tenant_id == tenant_id, Cliente.codigo == codigo_default,
        ).first()

    if not cliente:
        res.warnings.append("No se encontró cliente")
        return res

    lista_id = cliente.lista_precios_id

    unidades_db = db.query(UnidadEntrega).filter(
        UnidadEntrega.contrato_id == contrato.id,
        UnidadEntrega.activa.is_(True),
    ).all()
    unidad_candidates = {u.id: u.nombre for u in unidades_db}

    # Agrupar rows por unidad
    grouped: dict[str, list[PedidoRowIn]] = {}
    for row in rows:
        grouped.setdefault(row.unidad_nombre, []).append(row)

    for unidad_nombre, urows in grouped.items():
        m = best_match(unidad_nombre, unidad_candidates, threshold=fuzzy_threshold)
        if not m:
            res.unidades_sin_match.append(unidad_nombre)
            continue

        unidad_db = next((u for u in unidades_db if u.id == m.target_id), None)
        if not unidad_db:
            continue

        # Existing check
        existing = db.query(Pedido).filter(
            Pedido.tenant_id == tenant_id,
            Pedido.fecha_pedido == fecha,
            Pedido.unidad_entrega_id == unidad_db.id,
            Pedido.deleted_at.is_(None),
        ).first()

        if existing and not force_overwrite:
            res.pedidos_skipped.append({
                "unidad_nombre": unidad_db.nombre,
                "pedido_id": str(existing.id),
                "reason": "ya existe (force_overwrite=false)",
            })
            continue

        if existing and force_overwrite:
            # Borra líneas y resetea
            db.query(LineaPedido).filter(LineaPedido.pedido_id == existing.id).delete()
            db.delete(existing)
            db.flush()

        unidad_warns = []
        if m.method != "exact":
            unidad_warns.append({
                "type": "unidad_fuzzy_match",
                "input": unidad_nombre,
                "matched": unidad_db.nombre,
                "method": m.method,
                "score": m.score,
            })

        ped = Pedido(
            tenant_id=tenant_id,
            contrato_lote_id=lote.id if lote else None,
            cliente_facturacion_id=cliente.id,
            unidad_entrega_id=unidad_db.id,
            fecha_pedido=fecha,
            estado="CONFIRMADO",
            canal=canal,
            raw_payload=raw_payload,
            ai_confidence=Decimal(str(round(m.score / 100.0, 4))),
            ai_warnings=unidad_warns,
        )
        db.add(ped)
        db.flush()

        subtotal = Decimal("0")
        any_unmatched_line = False
        for idx, row in enumerate(urows, start=1):
            producto = _resolve_producto(db, tenant_id, row.alimento)
            if not producto:
                res.lineas_sin_match.append({
                    "unidad_nombre": unidad_db.nombre,
                    "alimento": row.alimento,
                    "cantidad": float(row.cantidad),
                })
                any_unmatched_line = True
                # Guardamos la línea sin producto_id pero con texto_original
                db.add(LineaPedido(
                    pedido_id=ped.id,
                    numero_linea=idx,
                    producto_id=None,
                    presentacion=row.presentacion or "KILO",
                    cantidad_solicitada=row.cantidad,
                    precio_unitario=Decimal("0"),
                    importe=Decimal("0"),
                    texto_original=row.alimento,
                ))
                continue

            precio = _resolve_precio(db, lista_id, producto.id, row.presentacion or "KILO") if lista_id else None
            precio = precio or Decimal("0")
            cantidad = Decimal(str(row.cantidad))
            importe = (cantidad * precio).quantize(Decimal("0.0001"))
            subtotal += importe

            db.add(LineaPedido(
                pedido_id=ped.id,
                numero_linea=idx,
                producto_id=producto.id,
                presentacion=row.presentacion or producto.presentacion_default or "KILO",
                cantidad_solicitada=cantidad,
                precio_unitario=precio,
                importe=importe,
                texto_original=row.alimento,
                ai_match_confidence=Decimal("1") if normalize(producto.nombre) == normalize(row.alimento) else Decimal("0.85"),
            ))

        ped.subtotal = subtotal
        ped.total = subtotal
        ped.requires_review = any_unmatched_line or m.score < 95.0

        res.pedidos_creados.append(PedidoBuilt(
            pedido_id=ped.id,
            folio_interno=ped.folio_interno,
            unidad_entrega_id=unidad_db.id,
            unidad_nombre=unidad_db.nombre,
            cliente_id=cliente.id,
            fecha=fecha,
            total=subtotal,
            lineas_count=len(urows),
            requires_review=bool(ped.requires_review),
        ))

    db.commit()
    return res
