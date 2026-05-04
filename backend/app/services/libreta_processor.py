"""Procesador de libreta — pedidos de comedores SUREÑA desde foto.

A diferencia del Excel BD (formato fijo del cliente EHMO), la libreta es
una foto de papel escrito a mano. La extraccion la hace Claude Vision
desde el chat (en accion_payload), y este executor solo ejecuta la
creacion de pedidos en DB + genera PDFs.

Espera `accion_payload` con shape:
    {
      "fecha_iso": "2026-04-30",  # o "fecha_entrega": "2026-04-30"
      "destinos": [
        {
          "destino": "Comedor Patria",
          "productos": [
            {"alimento": "Papas", "cantidad": 50, "presentacion": "Kilo"},
            {"alimento": "Sandías", "cantidad": 8, "presentacion": "Pieza"},
            ...
          ]
        },
        ...
      ]
    }
"""
from __future__ import annotations

import logging
from datetime import date as date_cls
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .pedidos import PedidoRowIn, from_batch_rows
from .pdf_generators import (
    generar_pedido_pdf, generar_lista_compras_pdf, generar_lista_compras_xlsx,
)
from .drive import upload_file

log = logging.getLogger(__name__)


def procesar_libreta(
    db: Session,
    tenant_id: UUID,
    payload: dict,
    *,
    cliente_id: Optional[UUID] = None,
    output_dir: Optional[Path] = None,
    upload_drive: bool = True,
) -> dict:
    """Procesa la libreta extraida por la AI.

    Returns dict con pedidos_creados, PDFs, links Drive.
    """
    fecha_iso = payload.get("fecha_iso") or payload.get("fecha_entrega")
    if not fecha_iso:
        return {"ejecutado": False, "razon": "fecha_iso ausente"}

    try:
        fecha = date_cls.fromisoformat(fecha_iso)
    except ValueError:
        return {"ejecutado": False, "razon": f"fecha_iso invalida: {fecha_iso}"}

    destinos = payload.get("destinos") or []
    if not destinos:
        return {"ejecutado": False, "razon": "sin destinos"}

    # Construir rows desde destinos -> productos
    rows: list[PedidoRowIn] = []
    for d in destinos:
        unidad = d.get("destino")
        if not unidad:
            continue
        for p in d.get("productos", []):
            alimento = p.get("alimento")
            cantidad = p.get("cantidad")
            if not alimento or cantidad is None:
                continue
            try:
                qty = Decimal(str(cantidad))
                if qty <= 0:
                    continue
            except Exception:
                continue
            rows.append(PedidoRowIn(
                unidad_nombre=unidad,
                alimento=alimento,
                cantidad=qty,
                presentacion=(p.get("presentacion") or "KILO").upper(),
            ))

    if not rows:
        return {"ejecutado": False, "razon": "sin filas validas"}

    # Crear pedidos via from_batch_rows (mismo flow que Excel BD)
    batch = from_batch_rows(
        db=db,
        tenant_id=tenant_id,
        fecha=fecha,
        rows=rows,
        canal="LIBRETA_FOTO",
        cliente_id=cliente_id,
        force_overwrite=False,
        raw_payload={
            "source": "libreta_chat",
            "destinos_count": len(destinos),
        },
    )

    # Generar PDFs
    output_dir = Path(output_dir or f"/tmp/cadena_libreta/{fecha_iso}")
    output_dir.mkdir(parents=True, exist_ok=True)
    items_pdf = [
        {
            "unidad": r.unidad_nombre,
            "alimento": r.alimento,
            "presentacion": r.presentacion,
            "cantidad": float(r.cantidad),
        }
        for r in rows
    ]

    pedido_pdf = output_dir / f"Pedido {fecha_iso} Comedores.pdf"
    lista_pdf = output_dir / f"Lista de Compras {fecha_iso} Comedores.pdf"
    lista_xlsx = output_dir / f"Lista de Compras {fecha_iso} Comedores.xlsx"

    docs: list[dict] = []
    try:
        generar_pedido_pdf(
            items_pdf, fecha_iso, pedido_pdf,
            subtitulo="Comedores Humanitarios",
        )
        docs.append({"tipo": "PEDIDO_PDF", "path": pedido_pdf})
    except Exception as e:
        log.exception(f"PDF pedido fallo: {e}")

    try:
        generar_lista_compras_pdf(items_pdf, fecha_iso, lista_pdf)
        docs.append({"tipo": "LISTA_COMPRAS_PDF", "path": lista_pdf})
    except Exception as e:
        log.exception(f"Lista compras PDF fallo: {e}")

    try:
        generar_lista_compras_xlsx(items_pdf, fecha_iso, lista_xlsx)
        docs.append({"tipo": "LISTA_COMPRAS_XLSX", "path": lista_xlsx})
    except Exception as e:
        log.exception(f"Lista compras XLSX fallo: {e}")

    # Subir a Drive
    if upload_drive:
        for d in docs:
            try:
                resp = upload_file(d["path"], subfolder=fecha_iso)
                if resp:
                    d["drive_url"] = resp.get("link")
            except Exception:
                pass

    return {
        "ejecutado": True,
        "fecha_iso": fecha_iso,
        "destinos_count": len(destinos),
        "pedidos_creados": [
            {
                "pedido_id": str(p.pedido_id),
                "folio_interno": p.folio_interno,
                "unidad_nombre": p.unidad_nombre,
                "lineas_count": p.lineas_count,
                "total": float(p.total),
            }
            for p in batch.pedidos_creados
        ],
        "pedidos_skipped": batch.pedidos_skipped,
        "unidades_sin_match": batch.unidades_sin_match,
        "lineas_sin_match_count": len(batch.lineas_sin_match),
        "documentos": [
            {
                "tipo": d["tipo"],
                "nombre": d["path"].name,
                "drive_url": d.get("drive_url"),
                "local_path": str(d["path"]),
            }
            for d in docs
        ],
    }
