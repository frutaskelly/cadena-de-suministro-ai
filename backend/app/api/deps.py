"""Dependencies para FastAPI: db session, current_tenant_id."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.db import SessionLocal


def get_db_session(x_tenant_id: Optional[str] = Header(None)) -> Session:
    """Yield session con app.current_tenant_id seteado para RLS.

    En producción, x_tenant_id viene de claims del JWT (no de header directo).
    Por ahora, header explícito para desarrollo.
    """
    db = SessionLocal()
    try:
        if x_tenant_id:
            try:
                UUID(x_tenant_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="x-tenant-id debe ser UUID válido")
            db.execute(text("SET LOCAL app.current_tenant_id = :tid"), {"tid": x_tenant_id})
        yield db
    finally:
        db.close()


def require_tenant(x_tenant_id: Optional[str] = Header(None)) -> UUID:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Header x-tenant-id requerido")
    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="x-tenant-id inválido")
