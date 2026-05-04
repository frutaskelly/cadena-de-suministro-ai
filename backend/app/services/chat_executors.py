"""Ejecutores de las acciones que el chat AI extrae (Phase 1 + 2 ports v1).

Acciones soportadas:
- procesar_archivo  : Excel BD -> pedidos + PDFs + Drive
- procesar_libreta  : foto libreta -> pedidos comedores + PDFs + Drive
- registrar_pesos   : actualiza cantidad_surtida en lineas pedido
- modificar_pedido  : cambia cantidades en pedido existente
- ajuste_entrega    : pesos reales o cancelacion in-situ
- extras_pedido     : agrega lineas a pedido existente
- emitir_remisiones : genera notas remision PDF para pedidos del dia
- generar_relacion  : PDF + XLSX consolidado del dia
"""
from __future__ import annotations

import base64
import logging
import tempfile
from datetime import date as date_cls, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import (
    AgenteWhatsapp, ChatConversacion, ChatMensaje, Cliente, DocumentoGenerado,
    LineaPedido, Pedido, Producto, Remision,
)
from .excel_bd_processor import procesar_excel_bd, ExcelBDResult
from .libreta_processor import procesar_libreta
from .nota_remision_pdf import generar_nota_remision_pdf
from .relacion_documentos import generar_relacion_pdf, generar_relacion_xlsx
from .drive import upload_file
from .base_maestra_builder import build_base_maestra

log = logging.getLogger(__name__)

EXCEL_MIMES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",
}


def _save_attachment_to_temp(att: dict) -> Optional[Path]:
    data = att.get("data_b64")
    if not data:
        return None
    nombre = att.get("nombre", "attachment")
    suffix = Path(nombre).suffix or ".bin"
    tmpdir = Path(tempfile.gettempdir()) / "cadena_chat_uploads"
    tmpdir.mkdir(parents=True, exist_ok=True)
    tmp = tmpdir / f"{Path(nombre).stem}_{tempfile._RandomNameSequence().__next__()}{suffix}"
    with open(tmp, "wb") as f:
        f.write(base64.b64decode(data))
    return tmp


def _register_doc(
    db: Session,
    *,
    tenant_id: UUID,
    agente_id: Optional[UUID],
    tipo: str,
    nombre: str,
    fecha: Optional[date_cls],
    drive_url: Optional[str],
    local_path: Optional[Path],
    pedido_id: Optional[UUID] = None,
    remision_id: Optional[UUID] = None,
    extra_meta: Optional[dict] = None,
):
    size = (
        Path(local_path).stat().st_size
        if local_path and Path(local_path).exists() else 0
    )
    meta = {"local_path": str(local_path) if local_path else None}
    if extra_meta:
        meta.update(extra_meta)
    doc = DocumentoGenerado(
        tenant_id=tenant_id,
        agente_id=agente_id,
        pedido_id=pedido_id,
        remision_id=remision_id,
        tipo_documento=tipo,
        nombre_archivo=nombre,
        fecha_documento=fecha,
        url_storage=drive_url,
        bytes=size,
        metadata_doc=meta,
    )
    db.add(doc)
    return doc


# ─── procesar_archivo (Excel BD) ───────────────────────────────────────
def execute_procesar_archivo(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    excel_att = None
    for att in (user_message.adjuntos or []):
        mime = att.get("mime", "")
        nombre = att.get("nombre", "")
        if mime in EXCEL_MIMES or nombre.lower().endswith((".xlsx", ".xls")):
            excel_att = att
            break
    if not excel_att:
        out["razon"] = "no_excel_attachment"
        return out

    tmp = _save_attachment_to_temp(excel_att)
    if not tmp:
        out["razon"] = "attachment_sin_data"
        return out

    cliente_id = None
    if conversacion.agente_id:
        agente = db.get(AgenteWhatsapp, conversacion.agente_id)
        if agente and agente.cliente_id:
            cliente_id = agente.cliente_id

    try:
        result: ExcelBDResult = procesar_excel_bd(
            db=db, tenant_id=tenant_id,
            excel_path=tmp, canal="EXCEL_BD",
            cliente_id=cliente_id, upload_drive=True,
        )
    except Exception as e:
        log.exception("excel_bd_processor fallo")
        out["razon"] = f"processor_error: {e}"
        return out

    fecha_doc = date_cls.fromisoformat(result.fecha_iso)
    docs_meta = [
        ("PEDIDO_PDF", result.pedido_pdf_path, result.pedido_pdf_drive_url),
        ("LISTA_COMPRAS_PDF", result.lista_compras_pdf_path, result.lista_compras_pdf_drive_url),
        ("LISTA_COMPRAS_XLSX", result.lista_compras_xlsx_path, result.lista_compras_xlsx_drive_url),
    ]
    docs_creados = []
    for tipo, local_path, drive_url in docs_meta:
        if not local_path:
            continue
        nombre = Path(local_path).name
        _register_doc(
            db, tenant_id=tenant_id, agente_id=conversacion.agente_id,
            tipo=tipo, nombre=nombre, fecha=fecha_doc,
            drive_url=drive_url, local_path=Path(local_path),
            extra_meta={
                "source": "chat_excel_bd",
                "conversacion_id": str(conversacion.id),
                "pedidos_creados": len(result.pedidos_creados),
            },
        )
        docs_creados.append({
            "tipo": tipo, "nombre": nombre,
            "drive_url": drive_url, "local_path": local_path,
        })
    db.commit()

    out["ejecutado"] = True
    out["result"] = {
        "fecha_iso": result.fecha_iso,
        "fecha_legible": result.fecha_legible,
        "pedidos_creados": len(result.pedidos_creados),
        "lineas_total": sum(p["lineas_count"] for p in result.pedidos_creados),
        "warnings": result.warnings,
        "unidades_sin_match": result.unidades_sin_match,
        "lineas_sin_match_count": len(result.lineas_sin_match),
    }
    out["documentos"] = docs_creados
    return out


# ─── procesar_libreta (foto comedores) ─────────────────────────────────
def execute_procesar_libreta(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    if not accion_payload:
        out["razon"] = "sin_payload"
        return out

    cliente_id = None
    if conversacion.agente_id:
        agente = db.get(AgenteWhatsapp, conversacion.agente_id)
        if agente and agente.cliente_id:
            cliente_id = agente.cliente_id

    try:
        r = procesar_libreta(
            db=db, tenant_id=tenant_id,
            payload=accion_payload, cliente_id=cliente_id,
        )
    except Exception as e:
        log.exception("libreta_processor fallo")
        out["razon"] = f"processor_error: {e}"
        return out

    if not r.get("ejecutado"):
        out["razon"] = r.get("razon", "libreta no ejecutada")
        return out

    fecha_doc = date_cls.fromisoformat(r["fecha_iso"])
    for d in r["documentos"]:
        _register_doc(
            db, tenant_id=tenant_id, agente_id=conversacion.agente_id,
            tipo=d["tipo"], nombre=d["nombre"], fecha=fecha_doc,
            drive_url=d.get("drive_url"),
            local_path=Path(d["local_path"]) if d.get("local_path") else None,
            extra_meta={
                "source": "chat_libreta",
                "conversacion_id": str(conversacion.id),
                "destinos": r.get("destinos_count"),
            },
        )
    db.commit()

    out["ejecutado"] = True
    out["result"] = {
        "fecha_iso": r["fecha_iso"],
        "destinos_count": r["destinos_count"],
        "pedidos_creados": len(r["pedidos_creados"]),
        "lineas_total": sum(p["lineas_count"] for p in r["pedidos_creados"]),
        "unidades_sin_match": r["unidades_sin_match"],
        "lineas_sin_match_count": r["lineas_sin_match_count"],
    }
    out["documentos"] = r["documentos"]
    return out


# ─── registrar_pesos: actualizar cantidad_surtida ──────────────────────
def execute_registrar_pesos(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    """payload: {fecha_iso, pesos: [{destino, alimento, kg}]}."""
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    if not accion_payload:
        out["razon"] = "sin_payload"
        return out

    fecha_iso = accion_payload.get("fecha_iso")
    pesos = accion_payload.get("pesos") or []
    if not fecha_iso or not pesos:
        out["razon"] = "fecha_iso o pesos ausentes"
        return out

    try:
        fecha = date_cls.fromisoformat(fecha_iso)
    except ValueError:
        out["razon"] = f"fecha_iso invalida: {fecha_iso}"
        return out

    actualizadas = 0
    no_match = []
    for entry in pesos:
        destino = (entry.get("destino") or "").lower()
        alimento = (entry.get("alimento") or "").lower()
        kg = entry.get("kg")
        if not destino or not alimento or kg is None:
            continue
        # Buscar lineas: pedido de la fecha + unidad similar + producto similar
        from sqlalchemy import or_, func
        q = (
            db.query(LineaPedido, Pedido, Producto)
            .join(Pedido, Pedido.id == LineaPedido.pedido_id)
            .join(Producto, Producto.id == LineaPedido.producto_id)
            .filter(
                Pedido.tenant_id == tenant_id,
                Pedido.fecha_pedido == fecha,
            )
        )
        rows = q.all()
        match_row = None
        for lp, ped, prod in rows:
            unidad_nombre = ""
            if ped.unidad_entrega_id:
                from ..models import UnidadEntrega
                u = db.get(UnidadEntrega, ped.unidad_entrega_id)
                unidad_nombre = (u.nombre if u else "").lower()
            if destino in unidad_nombre or unidad_nombre in destino:
                if alimento in prod.nombre.lower() or prod.nombre.lower() in alimento:
                    match_row = lp
                    break
        if match_row:
            try:
                match_row.cantidad_surtida = Decimal(str(kg))
                # recalcula importe
                if match_row.precio_unitario:
                    match_row.importe = match_row.cantidad_surtida * match_row.precio_unitario
                actualizadas += 1
            except Exception:
                no_match.append(f"{destino}/{alimento}")
        else:
            no_match.append(f"{destino}/{alimento}")

    db.commit()
    out["ejecutado"] = True
    out["result"] = {
        "fecha_iso": fecha_iso,
        "lineas_actualizadas": actualizadas,
        "no_match": no_match,
    }
    return out


# ─── modificar_pedido / ajuste_entrega / extras_pedido ─────────────────
def execute_modificar_pedido(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    """payload: {pedido_id|folio, cambios: [{linea_id|alimento, cantidad?, precio?, eliminar?}]}.
    O: {fecha_iso, destino, cambios}.
    """
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    if not accion_payload:
        out["razon"] = "sin_payload"
        return out

    cambios = accion_payload.get("cambios") or []
    if not cambios:
        out["razon"] = "sin_cambios"
        return out

    # Resolver pedido objetivo
    pedido_id = accion_payload.get("pedido_id")
    folio = accion_payload.get("folio")
    fecha_iso = accion_payload.get("fecha_iso")
    destino = accion_payload.get("destino")

    pedido = None
    if pedido_id:
        pedido = db.get(Pedido, pedido_id)
    elif folio:
        pedido = db.query(Pedido).filter(
            Pedido.tenant_id == tenant_id,
            Pedido.folio_interno == folio,
        ).first()
    elif fecha_iso and destino:
        from ..models import UnidadEntrega
        try:
            fecha = date_cls.fromisoformat(fecha_iso)
        except ValueError:
            out["razon"] = f"fecha invalida: {fecha_iso}"
            return out
        pedido = (
            db.query(Pedido)
            .join(UnidadEntrega, UnidadEntrega.id == Pedido.unidad_entrega_id)
            .filter(
                Pedido.tenant_id == tenant_id,
                Pedido.fecha_pedido == fecha,
                UnidadEntrega.nombre.ilike(f"%{destino}%"),
            )
            .first()
        )

    if not pedido:
        out["razon"] = "pedido_no_encontrado"
        return out

    aplicados = 0
    skipped = []
    for c in cambios:
        linea = None
        if c.get("linea_id"):
            linea = db.get(LineaPedido, c["linea_id"])
        elif c.get("alimento"):
            alimento_lower = c["alimento"].lower()
            for lp in pedido.lineas:
                if lp.producto_id:
                    prod = db.get(Producto, lp.producto_id)
                    if prod and (
                        alimento_lower in prod.nombre.lower()
                        or prod.nombre.lower() in alimento_lower
                    ):
                        linea = lp
                        break
        if not linea:
            skipped.append(c)
            continue

        if c.get("eliminar"):
            db.delete(linea)
            aplicados += 1
            continue

        if c.get("cantidad") is not None:
            try:
                linea.cantidad_solicitada = Decimal(str(c["cantidad"]))
                if linea.precio_unitario:
                    linea.importe = linea.cantidad_solicitada * linea.precio_unitario
                aplicados += 1
            except Exception:
                skipped.append(c)
                continue
        if c.get("precio") is not None:
            try:
                linea.precio_unitario = Decimal(str(c["precio"]))
                linea.importe = linea.cantidad_solicitada * linea.precio_unitario
            except Exception:
                pass

    # Recalcular total del pedido
    pedido.subtotal = sum(
        (lp.importe or Decimal(0)) for lp in pedido.lineas
        if lp not in db.deleted
    ) or Decimal(0)
    pedido.total = pedido.subtotal
    db.commit()

    out["ejecutado"] = True
    out["result"] = {
        "pedido_id": str(pedido.id),
        "folio": pedido.folio_interno,
        "cambios_aplicados": aplicados,
        "cambios_skipped": len(skipped),
        "nuevo_total": float(pedido.total),
    }
    return out


def execute_extras_pedido(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    """payload: {pedido_id|fecha+destino, extras: [{alimento, cantidad, presentacion?}]}."""
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    if not accion_payload:
        out["razon"] = "sin_payload"
        return out
    extras = accion_payload.get("extras") or []
    if not extras:
        out["razon"] = "sin_extras"
        return out

    pedido_id = accion_payload.get("pedido_id")
    folio = accion_payload.get("folio")
    fecha_iso = accion_payload.get("fecha_iso")
    destino = accion_payload.get("destino")

    pedido = None
    if pedido_id:
        pedido = db.get(Pedido, pedido_id)
    elif folio:
        pedido = db.query(Pedido).filter(
            Pedido.tenant_id == tenant_id,
            Pedido.folio_interno == folio,
        ).first()
    elif fecha_iso and destino:
        from ..models import UnidadEntrega
        try:
            fecha = date_cls.fromisoformat(fecha_iso)
        except ValueError:
            out["razon"] = f"fecha invalida"
            return out
        pedido = (
            db.query(Pedido)
            .join(UnidadEntrega, UnidadEntrega.id == Pedido.unidad_entrega_id)
            .filter(
                Pedido.tenant_id == tenant_id,
                Pedido.fecha_pedido == fecha,
                UnidadEntrega.nombre.ilike(f"%{destino}%"),
            )
            .first()
        )

    if not pedido:
        out["razon"] = "pedido_no_encontrado"
        return out

    # Para cada extra, agregar linea (fuzzy match producto)
    from .pedidos import _resolve_producto
    n_added = 0
    no_match = []
    next_num = (max((lp.numero_linea for lp in pedido.lineas), default=0) or 0) + 1

    for e in extras:
        alimento = e.get("alimento")
        cantidad = e.get("cantidad")
        if not alimento or cantidad is None:
            continue

        prod = _resolve_producto(db, tenant_id, alimento)
        if not prod:
            no_match.append(alimento)
            continue

        try:
            qty = Decimal(str(cantidad))
        except Exception:
            no_match.append(alimento)
            continue

        # Precio del producto en la lista del cliente
        precio = Decimal(0)
        if pedido.cliente_facturacion_id:
            cli = db.get(Cliente, pedido.cliente_facturacion_id)
            if cli and cli.lista_precios_id:
                from ..models import Precio
                pr = (
                    db.query(Precio)
                    .filter(
                        Precio.lista_id == cli.lista_precios_id,
                        Precio.producto_id == prod.id,
                    )
                    .first()
                )
                if pr:
                    precio = pr.precio_unitario

        new_line = LineaPedido(
            tenant_id=tenant_id,
            pedido_id=pedido.id,
            numero_linea=next_num,
            producto_id=prod.id,
            cantidad_solicitada=qty,
            presentacion=(e.get("presentacion") or "KILO").upper(),
            precio_unitario=precio,
            importe=qty * precio,
            texto_original=alimento,
            notas="Extra (chat)",
        )
        db.add(new_line)
        next_num += 1
        n_added += 1

    pedido.subtotal = sum(
        (lp.importe or Decimal(0)) for lp in pedido.lineas
    )
    pedido.total = pedido.subtotal
    db.commit()

    out["ejecutado"] = True
    out["result"] = {
        "pedido_id": str(pedido.id),
        "folio": pedido.folio_interno,
        "extras_agregados": n_added,
        "no_match": no_match,
        "nuevo_total": float(pedido.total),
    }
    return out


# ─── emitir_remisiones / generar_relacion ──────────────────────────────
def execute_emitir_remisiones(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    """Genera 1 PDF Nota de Remision por cada Remision CONFIRMADA del dia."""
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    payload = accion_payload or {}
    fecha_iso = payload.get("fecha_iso") or date_cls.today().isoformat()
    try:
        fecha = date_cls.fromisoformat(fecha_iso)
    except ValueError:
        out["razon"] = f"fecha_iso invalida: {fecha_iso}"
        return out

    remisiones = (
        db.query(Remision)
        .filter(
            Remision.tenant_id == tenant_id,
            Remision.fecha_generada == fecha,
            Remision.estado.in_(["CONFIRMADA", "FACTURADA"]),
        )
        .all()
    )
    if not remisiones:
        out["razon"] = f"sin_remisiones_para_{fecha_iso}"
        return out

    output_dir = Path(f"/tmp/cadena_notas_remision/{fecha_iso}")
    output_dir.mkdir(parents=True, exist_ok=True)

    docs = []
    for rem in remisiones:
        try:
            pdf_path = output_dir / f"Nota_{rem.folio}.pdf"
            generar_nota_remision_pdf(db, rem, pdf_path)
            drive_url = None
            try:
                resp = upload_file(pdf_path, subfolder=fecha_iso)
                if resp:
                    drive_url = resp.get("link")
            except Exception:
                pass

            _register_doc(
                db, tenant_id=tenant_id, agente_id=conversacion.agente_id,
                tipo="REMISION_PDF", nombre=pdf_path.name, fecha=fecha,
                drive_url=drive_url, local_path=pdf_path,
                remision_id=rem.id,
                extra_meta={
                    "source": "chat_emitir_remisiones",
                    "folio": rem.folio,
                    "total": float(rem.total or 0),
                },
            )
            docs.append({
                "tipo": "REMISION_PDF", "nombre": pdf_path.name,
                "drive_url": drive_url, "local_path": str(pdf_path),
                "folio": rem.folio,
            })
        except Exception as e:
            log.exception(f"error generando nota {rem.folio}")
    db.commit()

    out["ejecutado"] = True
    out["result"] = {
        "fecha_iso": fecha_iso,
        "remisiones_count": len(remisiones),
        "notas_generadas": len(docs),
    }
    out["documentos"] = docs
    return out


def execute_generar_relacion(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    """Genera Relacion PDF + XLSX consolidado del dia."""
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    payload = accion_payload or {}
    fecha_iso = payload.get("fecha_iso") or date_cls.today().isoformat()
    try:
        fecha = date_cls.fromisoformat(fecha_iso)
    except ValueError:
        out["razon"] = f"fecha invalida: {fecha_iso}"
        return out

    output_dir = Path(f"/tmp/cadena_relacion/{fecha_iso}")
    output_dir.mkdir(parents=True, exist_ok=True)
    docs = []

    try:
        pdf_path = output_dir / f"Relacion {fecha_iso}.pdf"
        generar_relacion_pdf(db, tenant_id, fecha, pdf_path)
        drive_url = None
        try:
            resp = upload_file(pdf_path, subfolder=fecha_iso)
            if resp:
                drive_url = resp.get("link")
        except Exception:
            pass
        _register_doc(
            db, tenant_id=tenant_id, agente_id=conversacion.agente_id,
            tipo="RELACION_PDF", nombre=pdf_path.name, fecha=fecha,
            drive_url=drive_url, local_path=pdf_path,
            extra_meta={"source": "chat_generar_relacion"},
        )
        docs.append({
            "tipo": "RELACION_PDF", "nombre": pdf_path.name,
            "drive_url": drive_url, "local_path": str(pdf_path),
        })
    except Exception as e:
        log.exception("relacion pdf fallo")

    try:
        xlsx_path = output_dir / f"Relacion {fecha_iso}.xlsx"
        generar_relacion_xlsx(db, tenant_id, fecha, xlsx_path)
        drive_url = None
        try:
            resp = upload_file(xlsx_path, subfolder=fecha_iso)
            if resp:
                drive_url = resp.get("link")
        except Exception:
            pass
        _register_doc(
            db, tenant_id=tenant_id, agente_id=conversacion.agente_id,
            tipo="RELACION_XLSX", nombre=xlsx_path.name, fecha=fecha,
            drive_url=drive_url, local_path=xlsx_path,
            extra_meta={"source": "chat_generar_relacion"},
        )
        docs.append({
            "tipo": "RELACION_XLSX", "nombre": xlsx_path.name,
            "drive_url": drive_url, "local_path": str(xlsx_path),
        })
    except Exception:
        log.exception("relacion xlsx fallo")
    db.commit()

    out["ejecutado"] = True
    out["result"] = {"fecha_iso": fecha_iso}
    out["documentos"] = docs
    return out


# ─── procesar_base_maestra ─────────────────────────────────────────────
def execute_procesar_base_maestra(
    db, tenant_id, conversacion, user_message, accion_payload=None
):
    """Genera Base Maestra a partir de un folder local.

    payload: {
      "source_folder": "/path/al/folder",
      "fecha_inicio": "2026-05-04",
      "fecha_fin": "2026-05-10",
      "base_anterior_path": "/path/Base maestra .xlsx" (opcional, cross-check),
    }
    """
    out = {"ejecutado": False, "razon": None, "result": None, "documentos": []}
    payload = accion_payload or {}
    source = payload.get("source_folder") or payload.get("folder")
    fi = payload.get("fecha_inicio")
    ff = payload.get("fecha_fin")
    base_ant = payload.get("base_anterior_path")

    if not source or not fi or not ff:
        out["razon"] = "Falta source_folder, fecha_inicio o fecha_fin"
        return out

    try:
        fecha_inicio = date_cls.fromisoformat(fi)
        fecha_fin = date_cls.fromisoformat(ff)
    except ValueError:
        out["razon"] = "Fechas invalidas (formato YYYY-MM-DD)"
        return out

    source_path = Path(source).expanduser()
    if not source_path.exists():
        out["razon"] = f"Folder no existe: {source_path}"
        return out

    # Crear el run en DB para audit
    from ..models import BaseMaestraRun
    run = BaseMaestraRun(
        tenant_id=tenant_id,
        fecha_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
        fecha_fin=datetime.combine(fecha_fin, datetime.min.time()),
        semana_label=f"{fecha_inicio.isoformat()} al {fecha_fin.isoformat()}",
        estado="EN_PROGRESO",
        source_folder=str(source_path),
        conversacion_id=conversacion.id,
    )
    db.add(run)
    db.flush()
    started = datetime.utcnow()

    try:
        output_dir = Path(f"/tmp/cadena_base_maestra/{fecha_inicio.isoformat()}_{fecha_fin.isoformat()}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"Base maestra {fecha_inicio.isoformat()} al {fecha_fin.isoformat()}.xlsx"

        result = build_base_maestra(
            source_folder=source_path,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            output_path=output_path,
            base_anterior=Path(base_ant) if base_ant else None,
        )
    except Exception as e:
        log.exception("base_maestra builder fallo")
        run.estado = "FALLIDA"
        run.detalle = {"error": str(e)[:500]}
        run.finished_at = datetime.utcnow()
        run.elapsed_ms = int((run.finished_at - started).total_seconds() * 1000)
        db.commit()
        out["razon"] = f"builder_error: {e}"
        return out

    # Subir a Drive
    drive_url = None
    try:
        resp = upload_file(
            output_path,
            subfolder=f"BaseMaestra_{fecha_inicio.isoformat()}",
        )
        if resp:
            drive_url = resp.get("link")
    except Exception:
        log.exception("Drive upload base maestra fallo")

    # Stats
    ok = sum(1 for h in result.hospitales if h.estado == "OK")
    warn = sum(1 for h in result.hospitales if h.estado == "WARN")
    fail = sum(1 for h in result.hospitales if h.estado == "FAIL")

    estado_final = "EXITOSA" if fail == 0 and warn == 0 else (
        "EXITOSA_CON_WARNINGS" if ok > 0 else "FALLIDA"
    )

    detalle = [
        {
            "hospital": h.nombre,
            "canonico": h.nombre_canonico,
            "estado": h.estado,
            "items": len(h.items),
            "archivos": h.archivos,
            "hojas": h.hojas_usadas,
            "warnings": h.warnings,
            "errors": h.errors,
        }
        for h in result.hospitales
    ]

    # Update run
    run.estado = estado_final
    run.archivos_count = sum(len(h.archivos) for h in result.hospitales)
    run.hospitales_ok = ok
    run.hospitales_warning = warn
    run.hospitales_fallidos = fail
    run.filas_bd = result.filas_bd
    run.output_local_path = str(output_path)
    run.output_drive_url = drive_url
    run.output_size_bytes = result.output_size
    run.diff_pct_vs_anterior = result.diff_pct_vs_anterior
    run.detalle = detalle
    run.finished_at = datetime.utcnow()
    run.elapsed_ms = int((run.finished_at - started).total_seconds() * 1000)

    # Registrar documento generado
    _register_doc(
        db,
        tenant_id=tenant_id,
        agente_id=conversacion.agente_id,
        tipo="BASE_MAESTRA_XLSX",
        nombre=output_path.name,
        fecha=fecha_inicio,
        drive_url=drive_url,
        local_path=output_path,
        extra_meta={
            "source": "chat_base_maestra",
            "run_id": str(run.id),
            "hospitales_ok": ok,
            "hospitales_warning": warn,
            "hospitales_fail": fail,
            "filas_bd": result.filas_bd,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
        },
    )
    db.commit()

    out["ejecutado"] = True
    out["result"] = {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "semana_label": result.semana_label,
        "filas_bd": result.filas_bd,
        "hospitales_total": len(result.hospitales),
        "hospitales_ok": ok,
        "hospitales_warning": warn,
        "hospitales_fail": fail,
        "diff_pct_vs_anterior": result.diff_pct_vs_anterior,
        "diff_resumen": result.diff_resumen,
        "detalle": detalle,
    }
    out["documentos"] = [{
        "tipo": "BASE_MAESTRA_XLSX",
        "nombre": output_path.name,
        "drive_url": drive_url,
        "local_path": str(output_path),
    }]
    return out


# ─── Dispatcher ─────────────────────────────────────────────────────────
ACTION_DISPATCH = {
    "procesar_archivo": execute_procesar_archivo,
    "procesar_excel": execute_procesar_archivo,
    "procesar_excel_bd": execute_procesar_archivo,
    "procesar_libreta": execute_procesar_libreta,
    "registrar_pesos": execute_registrar_pesos,
    "modificar_pedido": execute_modificar_pedido,
    "ajuste_entrega": execute_modificar_pedido,  # alias
    "extras_pedido": execute_extras_pedido,
    "emitir_remisiones": execute_emitir_remisiones,
    "consolidar_notas": execute_emitir_remisiones,  # alias
    "generar_relacion": execute_generar_relacion,
    "generar_relacion_surtido": execute_generar_relacion,  # alias
    "procesar_base_maestra": execute_procesar_base_maestra,
    "construir_base_maestra": execute_procesar_base_maestra,  # alias
    "generar_base_maestra": execute_procesar_base_maestra,  # alias
}


def execute_action(
    db: Session,
    tenant_id: UUID,
    conversacion: ChatConversacion,
    user_message: ChatMensaje,
    accion: str,
    accion_payload: Optional[dict] = None,
) -> dict:
    handler = ACTION_DISPATCH.get(accion)
    if not handler:
        return {
            "ejecutado": False,
            "razon": f"accion_no_implementada: {accion}",
            "result": None,
            "documentos": [],
        }
    return handler(db, tenant_id, conversacion, user_message, accion_payload)


def render_executor_summary(out: dict) -> str:
    """Genera mensaje humano + links markdown."""
    if not out.get("ejecutado"):
        return f"⚠️ No se ejecutó la acción: {out.get('razon')}"

    r = out.get("result") or {}
    docs = out.get("documentos") or []
    lines = []

    # Cabecera segun tipo de resultado
    if r.get("fecha_legible"):
        lines.append(f"✅ Procesado el pedido del **{r['fecha_legible']}**")
    elif r.get("fecha_iso"):
        lines.append(f"✅ Generado para **{r['fecha_iso']}**")
    else:
        lines.append("✅ Acción ejecutada")
    lines.append("")

    # Detalles segun campos
    if "pedidos_creados" in r:
        lines.append(f"- **{r['pedidos_creados']}** pedidos creados")
    if "lineas_total" in r:
        lines.append(f"- **{r['lineas_total']}** líneas totales")
    if "destinos_count" in r:
        lines.append(f"- **{r['destinos_count']}** destinos")
    if r.get("unidades_sin_match"):
        nombres = ", ".join(r["unidades_sin_match"][:3])
        suf = "…" if len(r["unidades_sin_match"]) > 3 else ""
        lines.append(f"- ⚠️ {len(r['unidades_sin_match'])} unidades sin match: {nombres}{suf}")
    if r.get("lineas_sin_match_count", 0) > 0:
        lines.append(f"- ⚠️ {r['lineas_sin_match_count']} líneas sin producto")
    if "lineas_actualizadas" in r:
        lines.append(f"- **{r['lineas_actualizadas']}** líneas actualizadas con peso real")
    if r.get("no_match"):
        lines.append(f"- ⚠️ no encontradas: {', '.join(r['no_match'][:5])}")
    if "cambios_aplicados" in r:
        lines.append(f"- **{r['cambios_aplicados']}** cambios aplicados (skipped: {r.get('cambios_skipped', 0)})")
        lines.append(f"- nuevo total del pedido: ${r.get('nuevo_total', 0):,.2f}")
    if "extras_agregados" in r:
        lines.append(f"- **{r['extras_agregados']}** extras agregados")
        lines.append(f"- nuevo total: ${r.get('nuevo_total', 0):,.2f}")
    if "remisiones_count" in r:
        lines.append(f"- **{r['remisiones_count']}** remisiones del día → **{r.get('notas_generadas', 0)}** notas generadas")

    # Base Maestra-specific
    if "hospitales_total" in r:
        lines.append(
            f"- Hospitales: **{r['hospitales_ok']} OK · {r['hospitales_warning']} con warnings · "
            f"{r['hospitales_fail']} fallidos** (de {r['hospitales_total']} totales)"
        )
        lines.append(f"- Filas BD generadas: **{r['filas_bd']:,}**")
        if r.get("diff_pct_vs_anterior") is not None:
            lines.append(
                f"- Diferencia vs base maestra anterior: **{r['diff_pct_vs_anterior']*100:.1f}%**"
            )
        # Detalle por hospital problematico
        det = r.get("detalle") or []
        problematicos = [d for d in det if d["estado"] != "OK"]
        if problematicos:
            lines.append("")
            lines.append("**Hospitales con problemas:**")
            for d in problematicos:
                primer_msg = (d.get("errors") or d.get("warnings") or [""])[0]
                if primer_msg:
                    primer_msg = primer_msg[:80] + ("…" if len(primer_msg) > 80 else "")
                lines.append(
                    f"- _{d['estado']}_ **{d['hospital']}**: {primer_msg}"
                )

    if docs:
        lines.append("")
        lines.append("**Documentos generados:**")
        labels = {
            "PEDIDO_PDF": "Pedido (PDF, hoja por hospital)",
            "PEDIDO_XLSX": "Pedido (Excel)",
            "LISTA_COMPRAS_PDF": "Lista de compras (PDF)",
            "LISTA_COMPRAS_XLSX": "Lista de compras (Excel)",
            "REMISION_PDF": "Nota de remisión",
            "RELACION_PDF": "Relación de documentos (PDF)",
            "RELACION_XLSX": "Relación de documentos (Excel)",
        }
        for d in docs:
            tipo_lbl = labels.get(d["tipo"], d["tipo"])
            folio = d.get("folio")
            label = f"{tipo_lbl} {folio}" if folio else tipo_lbl
            url = d.get("drive_url")
            if url:
                lines.append(f"- [{label}]({url})")
            else:
                lines.append(f"- {label} _(local — Drive no disponible)_")

    return "\n".join(lines)
