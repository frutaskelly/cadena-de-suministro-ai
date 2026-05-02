"""Tests del CFDI builder."""
import os

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.db import SessionLocal, engine
from app.models import Tenant, Pedido
from app.services.cfdi_builder import build_cfdi_from_pedido


@pytest.fixture(scope="module")
def db():
    if "DATABASE_URL" not in os.environ:
        pytest.skip("DATABASE_URL no seteada")
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(scope="module")
def tenant(db):
    t = db.query(Tenant).filter(Tenant.slug == "frutas-kelly").first()
    if not t:
        pytest.skip("Migración no corrida")
    return t


def test_build_cfdi_for_real_pedido(db, tenant):
    p = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.deleted_at.is_(None),
    ).first()
    if not p:
        pytest.skip("No hay pedidos")
    result = build_cfdi_from_pedido(db, p)
    assert result.payload is not None
    assert result.payload["CfdiType"] == "I"
    assert result.payload["Issuer"]["Rfc"] == tenant.rfc
    assert result.payload["Issuer"]["FiscalRegime"] == tenant.regimen_fiscal_sat
    assert result.payload["Receiver"]["Rfc"]
    assert len(result.payload["Items"]) > 0
    # Subtotal coincide con suma de items
    subtotal_sum = sum(it["Subtotal"] for it in result.payload["Items"])
    assert abs(result.payload["Subtotal"] - subtotal_sum) < 0.02


def test_cfdi_preview_endpoint(db, tenant):
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    p = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.deleted_at.is_(None),
    ).first()
    if not p:
        pytest.skip("No hay pedidos")
    r = client.get(
        f"/api/v1/pedidos/{p.id}/cfdi-preview",
        headers={"x-tenant-id": str(tenant.id)},
    )
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data
    assert "errors" in data
    assert "warnings" in data
    if data["ok"]:
        assert data["payload"] is not None


def test_cfdi_preview_404_for_unknown_pedido(db, tenant):
    from fastapi.testclient import TestClient
    from app.main import app
    from uuid import uuid4

    client = TestClient(app)
    r = client.get(
        f"/api/v1/pedidos/{uuid4()}/cfdi-preview",
        headers={"x-tenant-id": str(tenant.id)},
    )
    assert r.status_code == 404
