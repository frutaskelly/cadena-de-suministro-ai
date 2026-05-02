"""Importa sinónimos del agente legacy de WhatsApp a productos.sinonimos[].

El agente legacy (Whatsapp_agent/app/pricing.py) usa un dict _ALIAS_BUSQUEDA
para mapear términos como "tomate" → "jitomate saladet". Este script:

1. Lee los aliases del legacy
2. Para cada alias key → target, encuentra el producto que mejor matchea
   `target` (por nombre_normalizado, con normalización igual al agente)
3. Agrega el alias key a productos.sinonimos[] (sin duplicar)

Ejecutar:
    cd backend && source venv/bin/activate
    python ../scripts/import_sinonimos.py

Idempotente: se puede correr múltiples veces.
"""
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.db import SessionLocal
from app.models import Tenant, Producto


# Copiado literal de Whatsapp_agent/app/pricing.py (_ALIAS_BUSQUEDA)
ALIAS_BUSQUEDA = {
    "tomate": "jitomate saladet",
    "tomates": "jitomate saladet",
    "hierba buena": "hierbabuena",
    "hrerva buena": "hierbabuena",
    "yerba buena": "hierbabuena",
    "yerbabuena": "hierbabuena",
    "yierba buena": "hierbabuena",
    "yierbabuena": "hierbabuena",
    "chile jalapeno": "chile cuaresmeno",
    "jalapeno": "chile cuaresmeno",
}


def _normalize(s: str) -> str:
    s = (s or "").lower().strip()
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def find_producto(db, tenant_id, target: str) -> Producto | None:
    """Busca el mejor match para `target` entre productos del tenant.

    Estrategia:
      1. Match exacto sobre nombre_normalizado
      2. Match por containment (target dentro de nombre o viceversa)
      3. Match por palabras significativas en común
    """
    nt = _normalize(target)
    productos = db.query(Producto).filter(
        Producto.tenant_id == tenant_id,
        Producto.deleted_at.is_(None),
        Producto.activo.is_(True),
    ).all()

    # 1. Exact
    for p in productos:
        if _normalize(p.nombre) == nt:
            return p

    # 2. Containment
    for p in productos:
        n = _normalize(p.nombre)
        if nt in n or n in nt:
            return p

    # 3. Significant word overlap (>=4 chars)
    target_words = {w for w in nt.split() if len(w) >= 4}
    if not target_words:
        return None
    best = None
    best_score = 0
    for p in productos:
        n = _normalize(p.nombre)
        nwords = {w for w in n.split() if len(w) >= 4}
        score = len(target_words & nwords)
        if score > best_score:
            best_score = score
            best = p
    return best


def main():
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == "frutas-kelly").first()
        if not tenant:
            print("ERROR: tenant frutas-kelly no existe; corre la migración primero")
            sys.exit(1)
        print(f"Tenant: {tenant.id}\n")

        added = 0
        skipped_dup = 0
        not_found = []

        for alias_key, alias_target in ALIAS_BUSQUEDA.items():
            producto = find_producto(db, tenant.id, alias_target)
            if not producto:
                not_found.append((alias_key, alias_target))
                print(f"  [skip] '{alias_key}' → '{alias_target}': producto no encontrado")
                continue

            current = list(producto.sinonimos or [])
            if alias_key in current:
                skipped_dup += 1
                print(f"  [dup]  '{alias_key}' ya está en {producto.nombre}")
                continue

            current.append(alias_key)
            producto.sinonimos = current
            added += 1
            print(f"  [ok]   '{alias_key}' → {producto.nombre} (sku {producto.sku_interno})")

        db.commit()
        print(
            f"\nResumen: {added} agregados, {skipped_dup} duplicados, "
            f"{len(not_found)} sin match"
        )
        if not_found:
            print("Sin match:")
            for k, t in not_found:
                print(f"  - {k} → {t}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
