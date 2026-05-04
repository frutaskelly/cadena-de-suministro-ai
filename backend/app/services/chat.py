"""Servicio de chat con Claude — equivalente al ai_agent legacy v1.

Recibe mensaje del usuario (texto + adjuntos) y la historia de la
conversacion. Llama a Claude. Retorna la respuesta + metadata.

Soporta adjuntos:
- imagenes (jpg/png/webp/gif) -> input image type=base64
- PDFs -> input document type=base64
- texto/excel/csv -> texto plano dentro del mensaje
"""
from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from anthropic import Anthropic
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import ChatConversacion, ChatMensaje, AgenteWhatsapp

log = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

DEFAULT_SYSTEM_PROMPT = """Eres un asistente de operaciones para distribuidores
B2B/B2G de alimentos en Mexico (cliente principal: EHMO, surtidor de
hospitales y comedores). Ayudas a procesar pedidos, generar remisiones,
gestionar inventario, y dudas sobre productos/precios/CFDI.

═══════════════════════════════════════════════════════════════════════
REGLA CRITICA — ARCHIVOS XLSX (Excel)
═══════════════════════════════════════════════════════════════════════
Cuando recibas un archivo .xlsx (Excel BD del cliente), TU TAREA NO ES
LEER NI INTERPRETAR EL CONTENIDO. El sistema (no tu) tiene un parser
nativo openpyxl que extrae las filas correctas.

NO inventes nombres de productos, hospitales, fechas, ni cantidades.
NO listes los productos del archivo.

Cuando el usuario adjunta un .xlsx:
1. Responde brevemente: "Voy a procesar el Excel BD..."
2. AL FINAL del mensaje, agrega el bloque action exacto:

```action
{"accion": "procesar_archivo"}
```

El sistema entonces:
- Parsea el Excel con openpyxl
- Filtra por Lote 5 (FyV), excluye geograficos (Pichucalco, Palenque...)
- Crea pedidos en DB
- Genera PDFs (uno por hospital, lista compras consolidada, xlsx)
- Sube todo a Google Drive
- Te enviara un follow-up con los resultados reales

═══════════════════════════════════════════════════════════════════════
ACCIONES VALIDAS (siempre con campo "accion" exacto)
═══════════════════════════════════════════════════════════════════════
- procesar_archivo  -> Excel BD adjunto
- procesar_libreta  -> foto de libreta de comedores (Phase 2)
- registrar_pesos   -> reporte de pesos reales
- modificar_pedido  -> cambios sobre pedido existente
- consulta          -> sin accion (solo respuesta conversacional)

Formato OBLIGATORIO del bloque action (no uses "tipo", solo "accion"):

```action
{"accion": "procesar_archivo"}
```

═══════════════════════════════════════════════════════════════════════
ESTILO
═══════════════════════════════════════════════════════════════════════
- Directo, breve, profesional. Espanol mexicano.
- No te disculpes ni hagas preambulos.
- Si te falta info para una decision, pide solo lo critico.
- NO afirmes que un PDF/archivo existe hasta que el sistema confirme la
  generacion en un mensaje de follow-up."""


@dataclass
class ChatResponse:
    contenido: str
    accion: Optional[str] = None
    accion_payload: Optional[dict] = None
    tokens_in: int = 0
    tokens_out: int = 0
    elapsed_ms: int = 0
    model: str = DEFAULT_MODEL
    stop_reason: Optional[str] = None


def _build_history_for_claude(
    db: Session,
    conversacion_id: str,
    new_user_msg: str,
    new_attachments: list[dict],
) -> list[dict]:
    """Construye la lista de mensajes de Claude desde la historia."""
    history = (
        db.query(ChatMensaje)
        .filter(ChatMensaje.conversacion_id == conversacion_id)
        .order_by(ChatMensaje.created_at)
        .all()
    )

    messages: list[dict] = []
    for m in history:
        if m.role not in ("user", "assistant"):
            continue
        messages.append({
            "role": m.role,
            "content": m.contenido,
        })

    # Mensaje nuevo del usuario con adjuntos
    user_content: list[dict] = []
    if new_user_msg:
        user_content.append({"type": "text", "text": new_user_msg})

    for att in new_attachments or []:
        mime = att.get("mime", "")
        data_b64 = att.get("data_b64")
        if not data_b64:
            continue
        if mime.startswith("image/"):
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": data_b64,
                },
            })
        elif mime == "application/pdf":
            user_content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": data_b64,
                },
            })
        else:
            # Texto/CSV/Excel: incluir nombre como hint, los bytes no se mandan a Claude
            # (en MVP). Podemos parsearlos a texto despues.
            user_content.append({
                "type": "text",
                "text": f"[Adjunto: {att.get('nombre','archivo')} — {mime}, {att.get('size',0)} bytes]",
            })

    if not user_content:
        user_content = [{"type": "text", "text": "(sin contenido)"}]

    messages.append({"role": "user", "content": user_content})
    return messages


def _extract_action(text: str) -> tuple[Optional[str], Optional[dict]]:
    """Extrae bloque ```action {json}``` del mensaje del assistant.

    Tolera nombres alternativos: "accion", "action", "tipo", "intencion".
    """
    import json
    import re
    match = re.search(r"```action\s*\n?(.*?)```", text, re.DOTALL)
    if not match:
        return None, None
    try:
        payload = json.loads(match.group(1).strip())
    except (json.JSONDecodeError, ValueError):
        return None, None
    accion = (
        payload.pop("accion", None)
        or payload.pop("action", None)
        or payload.pop("tipo", None)
        or payload.pop("intencion", None)
    )
    return accion, payload


def chat_completion(
    db: Session,
    conversacion: ChatConversacion,
    user_message: str,
    attachments: list[dict] | None = None,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
) -> ChatResponse:
    """Llama a Claude con la historia + mensaje nuevo. Retorna respuesta."""
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY no configurado en backend/.env"
        )

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # System prompt: agente especifico si la conversacion lo tiene
    system_prompt = DEFAULT_SYSTEM_PROMPT
    if conversacion.agente_id:
        agente = db.query(AgenteWhatsapp).filter(
            AgenteWhatsapp.id == conversacion.agente_id
        ).first()
        if agente and agente.system_prompt_addendum:
            system_prompt = (
                DEFAULT_SYSTEM_PROMPT
                + "\n\n--- Especializacion del agente ---\n"
                + agente.system_prompt_addendum
            )

    messages = _build_history_for_claude(
        db, str(conversacion.id), user_message, attachments or []
    )

    t0 = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    elapsed_ms = int((time.time() - t0) * 1000)

    text_blocks = [b.text for b in resp.content if hasattr(b, "text")]
    contenido = "\n".join(text_blocks) if text_blocks else "(respuesta vacia)"

    accion, payload = _extract_action(contenido)

    return ChatResponse(
        contenido=contenido,
        accion=accion,
        accion_payload=payload,
        tokens_in=resp.usage.input_tokens,
        tokens_out=resp.usage.output_tokens,
        elapsed_ms=elapsed_ms,
        model=model,
        stop_reason=resp.stop_reason,
    )


def auto_titulo_conversacion(primer_mensaje: str, max_chars: int = 60) -> str:
    """Genera un titulo corto a partir del primer mensaje."""
    txt = (primer_mensaje or "").strip().splitlines()[0] if primer_mensaje else ""
    if len(txt) > max_chars:
        return txt[:max_chars - 1] + "…"
    return txt or "Nueva conversacion"
