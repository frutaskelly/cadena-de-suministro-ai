"""Endpoints del modulo Chat (Sprint 10)."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from ..deps import get_db_session, require_tenant
from ...models import ChatConversacion, ChatMensaje
from ...schemas import (
    ChatConversacionCreate, ChatConversacionOut, ChatConversacionDetail,
    ChatMensajeIn, ChatMensajeOut,
)
from ...services.chat import (
    chat_completion, auto_titulo_conversacion, ChatResponse,
)
from ...services.chat_executors import execute_action, render_executor_summary

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/conversaciones", response_model=List[ChatConversacionOut])
def list_conversaciones(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
    archivada: Optional[bool] = Query(False),
    limit: int = Query(100, le=500),
):
    q = db.query(ChatConversacion).filter(
        ChatConversacion.tenant_id == tenant_id
    )
    if archivada is not None:
        q = q.filter(ChatConversacion.archivada == archivada)
    return (
        q.order_by(ChatConversacion.ultima_actividad.desc())
        .limit(limit)
        .all()
    )


@router.post(
    "/conversaciones", status_code=201, response_model=ChatConversacionOut
)
def create_conversacion(
    payload: ChatConversacionCreate,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    conv = ChatConversacion(
        tenant_id=tenant_id,
        agente_id=payload.agente_id,
        titulo=payload.titulo or "Nueva conversacion",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get(
    "/conversaciones/{conv_id}",
    response_model=ChatConversacionDetail,
)
def get_conversacion(
    conv_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    conv = (
        db.query(ChatConversacion)
        .options(selectinload(ChatConversacion.mensajes))
        .filter(
            ChatConversacion.id == conv_id,
            ChatConversacion.tenant_id == tenant_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    return conv


@router.delete("/conversaciones/{conv_id}", status_code=204)
def delete_conversacion(
    conv_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    conv = db.query(ChatConversacion).filter(
        ChatConversacion.id == conv_id,
        ChatConversacion.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    db.delete(conv)
    db.commit()


@router.patch(
    "/conversaciones/{conv_id}",
    response_model=ChatConversacionOut,
)
def update_conversacion(
    conv_id: UUID,
    titulo: Optional[str] = None,
    archivada: Optional[bool] = None,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    conv = db.query(ChatConversacion).filter(
        ChatConversacion.id == conv_id,
        ChatConversacion.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    if titulo is not None:
        conv.titulo = titulo
    if archivada is not None:
        conv.archivada = archivada
    db.commit()
    db.refresh(conv)
    return conv


@router.post(
    "/conversaciones/{conv_id}/mensajes",
    response_model=ChatMensajeOut,
)
def send_mensaje(
    conv_id: UUID,
    payload: ChatMensajeIn,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    """Envia mensaje del usuario, llama Claude, retorna mensaje del assistant."""
    conv = db.query(ChatConversacion).filter(
        ChatConversacion.id == conv_id,
        ChatConversacion.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    # 1) Persistir mensaje user
    user_msg = ChatMensaje(
        tenant_id=tenant_id,
        conversacion_id=conv.id,
        role="user",
        contenido=payload.contenido or "",
        adjuntos=[a.model_dump() for a in payload.adjuntos],
    )
    db.add(user_msg)
    conv.mensajes_count = (conv.mensajes_count or 0) + 1
    conv.ultima_actividad = datetime.utcnow()

    # Auto-titulo si era el primer mensaje
    if conv.mensajes_count == 1 and (
        not conv.titulo or conv.titulo == "Nueva conversacion"
    ):
        conv.titulo = auto_titulo_conversacion(payload.contenido)
    db.flush()

    # 2) Llamar Claude
    try:
        ai_resp: ChatResponse = chat_completion(
            db=db,
            conversacion=conv,
            user_message=payload.contenido or "",
            attachments=[a.model_dump() for a in payload.adjuntos],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"codigo": "ai_error", "mensaje": str(e)[:200]},
        )

    # 3) Persistir respuesta assistant
    asst_msg = ChatMensaje(
        tenant_id=tenant_id,
        conversacion_id=conv.id,
        role="assistant",
        contenido=ai_resp.contenido,
        accion=ai_resp.accion,
        accion_payload=ai_resp.accion_payload,
        ai_metadata={
            "model": ai_resp.model,
            "stop_reason": ai_resp.stop_reason,
            "tokens_in": ai_resp.tokens_in,
            "tokens_out": ai_resp.tokens_out,
            "elapsed_ms": ai_resp.elapsed_ms,
        },
    )
    db.add(asst_msg)
    conv.mensajes_count += 1
    conv.tokens_in = (conv.tokens_in or 0) + ai_resp.tokens_in
    conv.tokens_out = (conv.tokens_out or 0) + ai_resp.tokens_out
    conv.ultima_actividad = datetime.utcnow()

    # 4) Ejecutar la accion si la AI decidio una y hay attachment
    if ai_resp.accion and user_msg.adjuntos:
        try:
            executor_out = execute_action(
                db=db,
                tenant_id=tenant_id,
                conversacion=conv,
                user_message=user_msg,
                accion=ai_resp.accion,
                accion_payload=ai_resp.accion_payload,
            )
            asst_msg.accion_resultado = executor_out
            if executor_out.get("ejecutado"):
                # Append summary del executor al contenido del mensaje assistant
                summary = render_executor_summary(executor_out)
                asst_msg.contenido = (
                    asst_msg.contenido.rstrip()
                    + "\n\n---\n\n"
                    + summary
                )
        except Exception as e:
            asst_msg.accion_resultado = {"error": str(e)[:300]}

    db.commit()
    db.refresh(asst_msg)
    return asst_msg
