"""Genera remisiones REALES a partir de los pedidos migrados desde la version 1.

En el legacy WhatsApp_agent, cada pedido confirmado produce una nota de
remision (PDF) con folio. Esos folios son los que migramos a `pedidos.folio_interno`.
En el modelo nuevo:
  - pedido (la captura del pedido)
  - remision (la nota de remision = entrega fisica)
  - factura (CFDI 4.0 timbrado, opcional)

Este script crea 1 Remision por pedido reusando el folio_interno como folio
de la remision. Estado:
  - pedido.estado = FACTURADO -> remision.estado = FACTURADA
  - pedido.estado = CONFIRMADO -> remision.estado = CONFIRMADA
  - otros -> remision.estado = GENERADA

Ejecutar:
    cd backend && source venv/bin/activate
    DATABASE_URL=... python ../scripts/generate_real_remisiones.py
"""
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))

from app.core.db import SessionLocal
from app.models import Tenant, Pedido, Remision, LineaRemision

ESTADO_MAP = {
    "FACTURADO": "FACTURADA",
    "CONFIRMADO": "CONFIRMADA",
    "EN_SURTIDO": "ENTREGADA",
    "ENVIADO": "EN_TRANSITO",
    "ENTREGADO": "CONFIRMADA",
    "BORRADOR": "GENERADA",
    "CANCELADO": "CANCELADA",
}


def main():
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == "frutas-kelly").first()
        if not tenant:
            print("ERROR: tenant frutas-kelly no existe")
            return

        pedidos = db.query(Pedido).filter(Pedido.tenant_id == tenant.id).all()
        print(f"Procesando {len(pedidos)} pedidos...")

        creadas = 0
        skipped = 0
        for p in pedidos:
            # Skip si ya hay remision para este pedido
            existing = db.query(Remision).filter(
                Remision.tenant_id == tenant.id,
                Remision.pedido_id == p.id,
            ).first()
            if existing:
                skipped += 1
                continue

            estado_remision = ESTADO_MAP.get(p.estado, "GENERADA")

            rem = Remision(
                tenant_id=tenant.id,
                folio=p.folio_interno or f"R-{str(p.id)[:8]}",
                pedido_id=p.id,
                cliente_id=p.cliente_facturacion_id,
                unidad_entrega_id=p.unidad_entrega_id,
                fecha_generada=p.fecha_pedido,
                fecha_entrega=(
                    datetime.combine(p.fecha_entrega, datetime.min.time())
                    if p.fecha_entrega else None
                ),
                fecha_facturada=(
                    datetime.combine(p.fecha_pedido, datetime.min.time())
                    if estado_remision == "FACTURADA" else None
                ),
                estado=estado_remision,
                subtotal=p.subtotal,
                iva_total=p.iva,
                total=p.total,
                notas=f"Generada automaticamente desde pedido {p.folio_interno or p.id}",
                raw_payload={
                    "source": "version1_legacy_migration",
                    "pedido_estado_origen": p.estado,
                },
            )
            db.add(rem)
            db.flush()  # para get rem.id

            # Migrar las lineas — solo las que tienen producto matcheado
            for lp in p.lineas:
                if not lp.producto_id:
                    continue
                lr = LineaRemision(
                    tenant_id=tenant.id,
                    remision_id=rem.id,
                    linea_pedido_id=lp.id,
                    producto_id=lp.producto_id,
                    cantidad_solicitada=lp.cantidad_solicitada or Decimal(0),
                    cantidad_entregada=lp.cantidad_surtida or lp.cantidad_solicitada or Decimal(0),
                    cantidad_facturada=(
                        lp.cantidad_surtida or lp.cantidad_solicitada
                        if estado_remision == "FACTURADA" else None
                    ),
                    presentacion=lp.presentacion or "KILO",
                    precio_unitario=lp.precio_unitario or Decimal(0),
                    importe=lp.importe or Decimal(0),
                )
                db.add(lr)
            creadas += 1

        db.commit()
        print(f"\nResumen:")
        print(f"  Remisiones creadas:   {creadas}")
        print(f"  Skipped (ya existian): {skipped}")

        # estado breakdown
        from sqlalchemy import func
        rows = db.query(Remision.estado, func.count(Remision.id)).filter(
            Remision.tenant_id == tenant.id
        ).group_by(Remision.estado).all()
        print(f"\nDistribucion por estado:")
        for estado, count in rows:
            print(f"  {estado}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
