"""Ejecutores de las acciones que el chat AI extrae.

Cuando un mensaje assistant retorna `accion=procesar_archivo` (u otra),
el chat invoca el executor correspondiente. El executor:
1. Valida el adjunto.
2. Lo guarda en disco temporal.
3. Llama el servicio correspondiente (excel_bd_processor, libreta_processor, etc.).
4. Registra DocumentoGenerado en DB con url_storage Drive.
5. Devuelve un resumen humano para enviar como nuevo mensaje del assistant.
"""
from __future__ import annotations

import base64
import logging
import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import (
    AgenteWhatsapp, ChatConversacion, ChatMensaje, DocumentoGenerado,
    Pedido,
)
from .excel_bd_processor import procesar_excel_bd, ExcelBDResult

log = logging.getLogger(__name__)

EXCEL_MIMES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",  # algunos uploads
}


def _save_attachment_to_temp(att: dict) -> Optional[Path]:
    """Guarda data_b64 a archivo temporal. Returns Path o None."""
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


def execute_procesar_archivo(
    db: Session,
    tenant_id: UUID,
    conversacion: ChatConversacion,
    user_message: ChatMensaje,
    accion_payload: Optional[dict] = None,
) -> dict:
    """Ejecuta la accion 'procesar_archivo' (Excel BD).

    Buscar un adjunto Excel en el mensaje del usuario. Si existe,
    procesarlo con excel_bd_processor.
    """
    out = {
        "ejecutado": False,
        "razon": None,
        "result": None,
        "documentos": [],
    }

    # 1) Detectar Excel attachment en el mensaje user
    adjuntos = user_message.adjuntos or []
    excel_att = None
    for att in adjuntos:
        mime = att.get("mime", "")
        nombre = att.get("nombre", "")
        if mime in EXCEL_MIMES or nombre.lower().endswith((".xlsx", ".xls")):
            excel_att = att
            break

    if not excel_att:
        out["razon"] = "no_excel_attachment"
        return out

    # 2) Volcar a disco
    tmp_path = _save_attachment_to_temp(excel_att)
    if not tmp_path:
        out["razon"] = "attachment_sin_data"
        return out

    log.info(f"chat_executor: procesando Excel BD desde chat {conversacion.id}")

    # 3) Determinar agente -> cliente_id
    cliente_id = None
    contrato_id = None
    if conversacion.agente_id:
        agente = db.get(AgenteWhatsapp, conversacion.agente_id)
        if agente and agente.cliente_id:
            cliente_id = agente.cliente_id

    # 4) Procesar
    try:
        result: ExcelBDResult = procesar_excel_bd(
            db=db,
            tenant_id=tenant_id,
            excel_path=tmp_path,
            canal="EXCEL_BD",
            cliente_id=cliente_id,
            contrato_id=contrato_id,
            upload_drive=True,
        )
    except Exception as e:
        log.exception("excel_bd_processor fallo")
        out["razon"] = f"processor_error: {e}"
        return out

    # 5) Registrar DocumentoGenerado para cada PDF/XLSX
    docs_creados = []
    documentos_meta = [
        ("PEDIDO_PDF", result.pedido_pdf_path, result.pedido_pdf_drive_url),
        ("LISTA_COMPRAS_PDF", result.lista_compras_pdf_path, result.lista_compras_pdf_drive_url),
        ("LISTA_COMPRAS_XLSX", result.lista_compras_xlsx_path, result.lista_compras_xlsx_drive_url),
    ]
    from datetime import date as date_cls
    fecha_doc = date_cls.fromisoformat(result.fecha_iso)

    for tipo, local_path, drive_url in documentos_meta:
        if not local_path:
            continue
        nombre_archivo = Path(local_path).name
        size = Path(local_path).stat().st_size if Path(local_path).exists() else 0

        doc = DocumentoGenerado(
            tenant_id=tenant_id,
            agente_id=conversacion.agente_id,
            tipo_documento=tipo,
            nombre_archivo=nombre_archivo,
            fecha_documento=fecha_doc,
            url_storage=drive_url,
            bytes=size,
            metadata_doc={
                "source": "chat_excel_bd",
                "conversacion_id": str(conversacion.id),
                "mensaje_id": str(user_message.id),
                "fecha_legible": result.fecha_legible,
                "pedidos_creados": len(result.pedidos_creados),
                "local_path": local_path,
            },
        )
        db.add(doc)
        docs_creados.append({
            "tipo": tipo,
            "nombre": nombre_archivo,
            "drive_url": drive_url,
            "local_path": local_path,
        })
    db.flush()
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


def execute_action(
    db: Session,
    tenant_id: UUID,
    conversacion: ChatConversacion,
    user_message: ChatMensaje,
    accion: str,
    accion_payload: Optional[dict] = None,
) -> dict:
    """Dispatcher: ejecuta la accion segun nombre."""
    if accion in ("procesar_archivo", "procesar_excel", "procesar_excel_bd"):
        return execute_procesar_archivo(
            db, tenant_id, conversacion, user_message, accion_payload
        )
    # Acciones aun no portadas (Phase 2):
    # - procesar_libreta (foto comedores)
    # - registrar_pesos
    # - modificar_pedido
    # - ajuste_entrega
    return {
        "ejecutado": False,
        "razon": f"accion_no_implementada: {accion}",
        "result": None,
        "documentos": [],
    }


def render_executor_summary(out: dict) -> str:
    """Genera un mensaje humano para que el assistant lo retorne al chat."""
    if not out.get("ejecutado"):
        return f"⚠️ No se ejecuto la accion: {out.get('razon')}"

    r = out["result"] or {}
    docs = out["documentos"] or []

    lines = [
        f"✅ Procesado el pedido del **{r.get('fecha_legible', '')}**",
        "",
        f"- **{r.get('pedidos_creados', 0)} pedidos** creados",
        f"- **{r.get('lineas_total', 0)} líneas** totales",
    ]
    if r.get("unidades_sin_match"):
        lines.append(
            f"- ⚠️ {len(r['unidades_sin_match'])} unidades sin match: "
            f"{', '.join(r['unidades_sin_match'][:3])}"
            + ("…" if len(r["unidades_sin_match"]) > 3 else "")
        )
    if r.get("lineas_sin_match_count", 0) > 0:
        lines.append(
            f"- ⚠️ {r['lineas_sin_match_count']} líneas sin producto del catálogo"
        )

    if docs:
        lines.append("")
        lines.append("**Documentos generados:**")
        for d in docs:
            tipo_label = {
                "PEDIDO_PDF": "Pedido (PDF, hoja por hospital)",
                "LISTA_COMPRAS_PDF": "Lista de compras (PDF)",
                "LISTA_COMPRAS_XLSX": "Lista de compras (Excel)",
            }.get(d["tipo"], d["tipo"])
            url = d.get("drive_url")
            if url:
                lines.append(f"- [{tipo_label}]({url})")
            else:
                lines.append(f"- {tipo_label} _(local: `{d.get('local_path')}` — Drive sin configurar)_")

    if r.get("warnings"):
        lines.append("")
        lines.append("**Avisos:**")
        for w in r["warnings"][:5]:
            lines.append(f"- {w}")

    return "\n".join(lines)
