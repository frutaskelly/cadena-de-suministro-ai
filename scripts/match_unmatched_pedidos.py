"""Re-procesa los pedidos históricos que no matchearon por typos en nombres.

La migración inicial deja sin match los hospitales con typos como:
  - 'Juan C Corzo' vs 'Juan C. Corzo'
  - 'de Las Casas' vs 'de las Casas'
  - 'Gónzalez' vs 'Gonzalez'

Este script usa fuzzy matching (rapidfuzz) para encontrar la unidad correcta
y crea los pedidos faltantes. Idempotente: salta los que ya existen.

Ejecutar:
    cd backend && source venv/bin/activate
    python ../scripts/match_unmatched_pedidos.py [--dry-run]
"""
import argparse
import json
import sys
import unicodedata
from datetime import datetime
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.db import SessionLocal
from app.models import (
    Tenant, Cliente, Contrato, ContratoLote, UnidadEntrega,
    Producto, Pedido, LineaPedido,
)
from app.services.fuzzy_match import best_match

AGENT = HERE.parent.parent / "Whatsapp_agent"
PEDIDOS_DIR = AGENT / "storage" / "pedidos_dia"


def _normalize(s: str) -> str:
    s = (s or "").lower().strip()
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def main(dry_run: bool = False):
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == "frutas-kelly").first()
        if not tenant:
            print("ERROR: tenant frutas-kelly no existe")
            return

        contrato_ehmo = db.query(Contrato).filter(
            Contrato.tenant_id == tenant.id,
            Contrato.contratante == "EHMO",
        ).first()
        contrato_surena = db.query(Contrato).filter(
            Contrato.tenant_id == tenant.id,
            Contrato.contratante == "SUREÑA",
        ).first()
        lote_ehmo = db.query(ContratoLote).filter(
            ContratoLote.contrato_id == contrato_ehmo.id,
        ).first()
        lote_surena = db.query(ContratoLote).filter(
            ContratoLote.contrato_id == contrato_surena.id,
        ).first()
        cli_ehmo = db.query(Cliente).filter(
            Cliente.tenant_id == tenant.id, Cliente.codigo == "EHMO",
        ).first()
        cli_surena = db.query(Cliente).filter(
            Cliente.tenant_id == tenant.id, Cliente.codigo == "SURENA",
        ).first()

        unidades_ehmo = db.query(UnidadEntrega).filter(
            UnidadEntrega.contrato_id == contrato_ehmo.id,
        ).all()
        unidades_surena = db.query(UnidadEntrega).filter(
            UnidadEntrega.contrato_id == contrato_surena.id,
        ).all()
        unidad_ctx = {}
        for u in unidades_ehmo:
            unidad_ctx[u.id] = (u, lote_ehmo, cli_ehmo, "EXCEL_BD")
        for u in unidades_surena:
            unidad_ctx[u.id] = (u, lote_surena, cli_surena, "LIBRETA_FOTO")

        # Build candidate dict: id → name
        candidates = {u.id: u.nombre for u in unidades_ehmo + unidades_surena}

        productos_idx = {
            p.nombre_normalizado: p
            for p in db.query(Producto).filter(Producto.tenant_id == tenant.id).all()
        }

        existing_pairs = {
            (p.fecha_pedido, p.unidad_entrega_id)
            for p in db.query(Pedido).filter(Pedido.tenant_id == tenant.id).all()
        }

        unmatched_in_json = []
        matched_via_fuzzy = []
        matched_low_conf = []
        created = 0

        for archivo in sorted(PEDIDOS_DIR.glob("*.json")):
            if archivo.name.startswith("."):
                continue
            try:
                data = json.load(open(archivo))
            except json.JSONDecodeError:
                continue
            fecha_str = data.get("fecha")
            if not fecha_str:
                continue
            fecha = datetime.fromisoformat(fecha_str).date()

            for nombre, info in data.get("hospitales", {}).items():
                m = best_match(nombre, candidates, threshold=80.0)
                if not m:
                    unmatched_in_json.append((fecha_str, nombre))
                    continue

                if (fecha, m.target_id) in existing_pairs:
                    continue

                # Si el nombre coincide bytewise (no solo case-insensitive),
                # la migración original ya lo procesó y lo saltó por otra razón
                # (ej. raw_payload nuevo). Mejor no duplicar.
                if m.target_name == nombre and m.method == "exact":
                    continue

                u, lote, cli, canal = unidad_ctx[m.target_id]
                report_line = (
                    f"  {fecha_str}  '{nombre}' → '{m.target_name}' "
                    f"({m.method}, score={m.score:.1f})"
                )
                if m.score < 90 and m.method == "fuzzy":
                    matched_low_conf.append(report_line)
                else:
                    matched_via_fuzzy.append(report_line)
                print(report_line)

                if dry_run:
                    continue

                estado_legacy = info.get("estado", "modificado")
                estado_map = {
                    "creado": "CONFIRMADO",
                    "modificado": "FACTURADO",
                    "ajustado": "FACTURADO",
                }
                estado = estado_map.get(estado_legacy, "CONFIRMADO")

                ped = Pedido(
                    tenant_id=tenant.id,
                    folio_interno=info.get("folio_remision"),
                    contrato_lote_id=lote.id,
                    cliente_facturacion_id=cli.id,
                    unidad_entrega_id=u.id,
                    fecha_pedido=fecha,
                    estado=estado,
                    canal=canal,
                    raw_payload={**info, "_fuzzy_match": {
                        "raw_name": nombre,
                        "matched_name": m.target_name,
                        "method": m.method,
                        "score": m.score,
                    }},
                    ai_confidence=Decimal(str(round(m.score / 100.0, 4))),
                    requires_review=(m.score < 95.0),
                )
                db.add(ped)
                db.flush()

                subtotal = Decimal("0")
                for idx, prod in enumerate(info.get("productos", [])):
                    alimento_norm = _normalize(prod.get("alimento", ""))
                    producto = None
                    for nombre_norm, pp in productos_idx.items():
                        if nombre_norm in alimento_norm or alimento_norm in nombre_norm:
                            producto = pp
                            break
                    cantidad = Decimal(str(prod.get("cantidad", 0)))
                    cantidad_orig = Decimal(str(prod.get("cantidad_original", cantidad)))
                    precio = Decimal(str(prod.get("precio_unitario", 0)))
                    importe = Decimal(str(prod.get("importe", cantidad * precio)))

                    db.add(LineaPedido(
                        pedido_id=ped.id,
                        numero_linea=idx + 1,
                        producto_id=producto.id if producto else None,
                        presentacion=prod.get("presentacion", "KILO"),
                        cantidad_solicitada=cantidad_orig,
                        cantidad_surtida=cantidad,
                        precio_unitario=precio,
                        importe=importe,
                        texto_original=prod.get("alimento"),
                    ))
                    subtotal += importe

                ped.subtotal = subtotal
                ped.total = subtotal
                created += 1

            if not dry_run:
                db.commit()

        print()
        print(f"Resumen:")
        print(f"  Matcheados via fuzzy:  {len(matched_via_fuzzy)}")
        print(f"  Matcheados low conf:   {len(matched_low_conf)} (requires_review=True)")
        print(f"  Sin match:             {len(unmatched_in_json)}")
        print(f"  Pedidos creados:       {created}{' (DRY RUN)' if dry_run else ''}")
        if unmatched_in_json:
            print(f"\nNombres aún sin match:")
            for f, n in unmatched_in_json:
                print(f"    {f}: {n!r}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
