"""Endpoints de agentes WhatsApp y documentos generados (Sprint 9)."""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_db_session, require_tenant
from ...models import AgenteWhatsapp, DocumentoGenerado
from ...schemas import AgenteWhatsappOut, DocumentoGeneradoOut

router_agentes = APIRouter(prefix="/agentes-whatsapp", tags=["agentes-whatsapp"])
router_docs = APIRouter(prefix="/documentos", tags=["documentos"])


@router_agentes.get("", response_model=List[AgenteWhatsappOut])
def list_agentes(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
    activo: Optional[bool] = Query(None),
):
    q = db.query(AgenteWhatsapp).filter(AgenteWhatsapp.tenant_id == tenant_id)
    if activo is not None:
        q = q.filter(AgenteWhatsapp.activo == activo)
    return q.order_by(AgenteWhatsapp.tipo, AgenteWhatsapp.nombre).all()


@router_agentes.get("/{agente_id}", response_model=AgenteWhatsappOut)
def get_agente(
    agente_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
):
    a = db.query(AgenteWhatsapp).filter(
        AgenteWhatsapp.id == agente_id,
        AgenteWhatsapp.tenant_id == tenant_id,
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    return a


@router_docs.get("", response_model=List[DocumentoGeneradoOut])
def list_documentos(
    db: Session = Depends(get_db_session),
    tenant_id: UUID = Depends(require_tenant),
    tipo_documento: Optional[str] = Query(None),
    pedido_id: Optional[UUID] = Query(None),
    remision_id: Optional[UUID] = Query(None),
    agente_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    limit: int = Query(200, le=2000),
    offset: int = Query(0, ge=0),
):
    q = db.query(DocumentoGenerado).filter(
        DocumentoGenerado.tenant_id == tenant_id
    )
    if tipo_documento:
        q = q.filter(DocumentoGenerado.tipo_documento == tipo_documento)
    if pedido_id:
        q = q.filter(DocumentoGenerado.pedido_id == pedido_id)
    if remision_id:
        q = q.filter(DocumentoGenerado.remision_id == remision_id)
    if agente_id:
        q = q.filter(DocumentoGenerado.agente_id == agente_id)
    if fecha_desde:
        q = q.filter(DocumentoGenerado.fecha_documento >= fecha_desde)
    if fecha_hasta:
        q = q.filter(DocumentoGenerado.fecha_documento <= fecha_hasta)
    return q.order_by(DocumentoGenerado.created_at.desc()).limit(limit).offset(offset).all()
