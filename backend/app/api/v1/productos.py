from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from ..deps import get_db_session, require_tenant
from ...models import Producto, ListaPrecios, Precio
from ...schemas import (
    ProductoCreate, ProductoOut, ProductoUpdate,
    ListaPreciosCreate, ListaPreciosOut, PrecioCreate, PrecioOut,
)
from ...services.pedidos import _resolve_producto, _resolve_precio
from ...services.clave_sat_classifier import (
    ClaveSatClassifier, ClassifierError, ClassifierConfigError,
)
from ...core.config import settings

router = APIRouter(prefix="/productos", tags=["productos"])


def _normalize(s: str) -> str:
    import unicodedata
    s = (s or "").lower().strip()
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


@router.post("", response_model=ProductoOut, status_code=201)
def create_producto(
    payload: ProductoCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    existing = db.query(Producto).filter(
        Producto.tenant_id == tenant_id,
        Producto.sku_interno == payload.sku_interno,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{payload.sku_interno}' ya existe")
    data = payload.model_dump()
    if not data.get("nombre_normalizado"):
        data["nombre_normalizado"] = _normalize(data["nombre"])
    p = Producto(**data, tenant_id=tenant_id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("", response_model=List[ProductoOut])
def list_productos(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    activo: Optional[bool] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    query = db.query(Producto).filter(
        Producto.tenant_id == tenant_id,
        Producto.deleted_at.is_(None),
    )
    if categoria:
        query = query.filter(Producto.categoria == categoria)
    if activo is not None:
        query = query.filter(Producto.activo == activo)
    if q:
        nq = _normalize(q)
        like = f"%{nq}%"
        # Match contra nombre_normalizado, sku, o cualquier elemento del array sinonimos
        query = query.filter(or_(
            Producto.nombre_normalizado.like(like),
            Producto.sku_interno.ilike(f"%{q}%"),
            Producto.sinonimos.any(nq),
        ))
    return query.order_by(Producto.nombre).offset(offset).limit(limit).all()


@router.get("/resolve")
def resolve_producto(
    alimento: str = Query(..., description="Texto libre del alimento"),
    lista_id: Optional[UUID] = Query(None, description="Si se manda, también devuelve precio"),
    presentacion: str = Query("KILO"),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Resuelve un alimento (texto libre) al producto del catálogo.

    Considera sinónimos, normalización (acentos/case), y containment.
    Si se manda `lista_id` también devuelve el precio.
    """
    p = _resolve_producto(db, tenant_id, alimento)
    if not p:
        return {"matched": False, "input": alimento, "producto": None, "precio": None}
    out = {
        "matched": True,
        "input": alimento,
        "producto": {
            "id": str(p.id),
            "sku": p.sku_interno,
            "nombre": p.nombre,
            "presentacion_default": p.presentacion_default,
            "categoria": p.categoria,
            "sinonimos": list(p.sinonimos or []),
            "clave_sat": p.clave_sat,
            "unidad_sat": p.unidad_sat,
        },
        "precio": None,
    }
    if lista_id:
        precio = _resolve_precio(db, lista_id, p.id, presentacion)
        if precio is not None:
            out["precio"] = {
                "lista_id": str(lista_id),
                "presentacion": presentacion,
                "precio_unitario": float(precio),
            }
    return out


@router.get("/{producto_id}", response_model=ProductoOut)
def get_producto(
    producto_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    p = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.tenant_id == tenant_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return p


@router.patch("/{producto_id}", response_model=ProductoOut)
def update_producto(
    producto_id: UUID,
    payload: ProductoUpdate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    p = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.tenant_id == tenant_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    if payload.nombre is not None:
        p.nombre_normalizado = _normalize(payload.nombre)
    db.commit()
    db.refresh(p)
    return p


@router.post("/{producto_id}/classify-clave-sat")
def classify_clave_sat(
    producto_id: UUID,
    apply: bool = Query(False, description="Si true, también persiste el resultado en producto.clave_sat"),
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Clasifica el producto con Claude (subset c_ClaveProdServ FyV).

    Si `apply=true`, persiste la nueva clave_sat en el producto.
    """
    p = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.tenant_id == tenant_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    classifier = ClaveSatClassifier(api_key=settings.ANTHROPIC_API_KEY)
    if not classifier.configured:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY no configurada en .env",
        )
    try:
        result = classifier.classify(
            nombre=p.nombre,
            descripcion=p.descripcion,
            categoria=p.categoria,
        )
    except (ClassifierError, ClassifierConfigError) as e:
        raise HTTPException(status_code=502, detail=f"Classifier error: {e}")

    out = {
        "producto_id": str(p.id),
        "current_clave_sat": p.clave_sat,
        "suggested_clave_sat": result.clave,
        "suggested_descripcion": result.descripcion,
        "confidence": result.confidence,
        "rationale": result.rationale,
        "applied": False,
    }
    if apply:
        p.clave_sat = result.clave
        db.commit()
        out["applied"] = True
    return out


# ─── Listas de precios ──────────────────────────────────────────────────────

listas_router = APIRouter(prefix="/listas-precios", tags=["listas-precios"])


@listas_router.post("", response_model=ListaPreciosOut, status_code=201)
def create_lista(
    payload: ListaPreciosCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    existing = db.query(ListaPrecios).filter(
        ListaPrecios.tenant_id == tenant_id,
        ListaPrecios.codigo == payload.codigo,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"código '{payload.codigo}' ya existe")
    l = ListaPrecios(**payload.model_dump(), tenant_id=tenant_id)
    db.add(l)
    db.commit()
    db.refresh(l)
    return l


@listas_router.get("", response_model=List[ListaPreciosOut])
def list_listas(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    return db.query(ListaPrecios).filter(ListaPrecios.tenant_id == tenant_id).all()


# ─── Precios ────────────────────────────────────────────────────────────────

precios_router = APIRouter(prefix="/precios", tags=["precios"])


@precios_router.post("", response_model=PrecioOut, status_code=201)
def create_precio(
    payload: PrecioCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    p = Precio(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@precios_router.get("/by-lista/{lista_id}", response_model=List[PrecioOut])
def list_precios_by_lista(
    lista_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    return db.query(Precio).filter(Precio.lista_id == lista_id).all()
