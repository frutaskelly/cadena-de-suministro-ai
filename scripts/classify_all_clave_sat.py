"""Clasifica clave_sat de todos los productos del tenant Frutas Kelly usando Claude.

Productos con clave_sat = "50202301" (genérico FyV) son candidatos a re-clasificar
a una clave más específica del subset definido en
`app/services/clave_sat_classifier.py:CLAVES_FYV`.

Requiere ANTHROPIC_API_KEY en backend/.env. Costo aprox: ~110 productos × ~200 tokens
con Haiku ≈ < $0.05 USD.

Modo de uso:
    cd backend && source venv/bin/activate
    python ../scripts/classify_all_clave_sat.py [--dry-run] [--apply] [--threshold 0.7]

- --dry-run (default): solo imprime sugerencias, no persiste
- --apply: persiste si confidence >= threshold
- --threshold (default 0.7): mínimo para auto-apply
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.db import SessionLocal
from app.core.config import settings
from app.models import Tenant, Producto
from app.services.clave_sat_classifier import (
    ClaveSatClassifier, ClassifierError, ClassifierConfigError,
)


def main(dry_run: bool, threshold: float, only_generic: bool):
    if not settings.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY no configurada en backend/.env")
        sys.exit(1)

    classifier = ClaveSatClassifier(api_key=settings.ANTHROPIC_API_KEY)
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == "frutas-kelly").first()
        if not tenant:
            print("ERROR: tenant frutas-kelly no existe")
            sys.exit(1)

        q = db.query(Producto).filter(
            Producto.tenant_id == tenant.id,
            Producto.deleted_at.is_(None),
            Producto.activo.is_(True),
        )
        if only_generic:
            q = q.filter(Producto.clave_sat == "50202301")
        productos = q.all()
        print(f"Tenant: {tenant.id}")
        print(f"Productos a clasificar: {len(productos)}")
        print(f"Modo: {'DRY RUN' if dry_run else f'APPLY (threshold {threshold})'}")
        print()

        applied = 0
        skipped_low_conf = 0
        errors = 0

        for i, p in enumerate(productos, 1):
            try:
                r = classifier.classify(
                    nombre=p.nombre,
                    descripcion=p.descripcion,
                    categoria=p.categoria,
                )
            except (ClassifierError, ClassifierConfigError) as e:
                errors += 1
                print(f"  [err] {p.nombre}: {e}")
                continue

            change = " (sin cambio)" if r.clave == p.clave_sat else f" (era {p.clave_sat})"
            print(f"  [{i:3d}/{len(productos)}] {p.nombre:35s} → {r.clave}{change}  "
                  f"conf={r.confidence:.2f}  {r.rationale[:60]}")

            if r.clave != p.clave_sat:
                if r.confidence < threshold:
                    skipped_low_conf += 1
                elif not dry_run:
                    p.clave_sat = r.clave
                    applied += 1

        if not dry_run:
            db.commit()

        print()
        print(f"Resumen: {applied} aplicados, {skipped_low_conf} bajo threshold, "
              f"{errors} errores. {'(DRY RUN)' if dry_run else ''}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Persistir cambios (default es dry-run)")
    parser.add_argument("--threshold", type=float, default=0.7,
                        help="Confidence mínima para auto-apply (0..1)")
    parser.add_argument("--all", action="store_true",
                        help="Clasificar TODOS los productos (default solo los genéricos 50202301)")
    args = parser.parse_args()

    main(
        dry_run=not args.apply,
        threshold=args.threshold,
        only_generic=not args.all,
    )
