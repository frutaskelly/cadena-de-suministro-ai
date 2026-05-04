"""Tests para conversiones catalogado <-> no-catalogado (Sprint 8)."""
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.main import app  # noqa: E402

client = TestClient(app)


def _get_tenant_id():
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE slug='frutas-kelly'")).fetchone()
        return str(row[0]) if row else None


@pytest.fixture(scope="module")
def tenant_id():
    tid = _get_tenant_id()
    if not tid:
        pytest.skip("Migración no corrida")
    return tid


@pytest.fixture(scope="module")
def two_productos(tenant_id):
    """Toma 2 productos distintos y limpia conversiones previas para tests idempotentes."""
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id FROM productos WHERE tenant_id=:t LIMIT 2"
        ), {"t": tenant_id}).fetchall()
        if len(rows) < 2:
            pytest.skip("Necesitan al menos 2 productos en el tenant")
        a, b = str(rows[0][0]), str(rows[1][0])
        # limpia conversiones previas con este par
        conn.execute(text(
            "DELETE FROM conversiones_producto "
            "WHERE tenant_id=:t AND producto_catalogado_id=:a AND producto_no_catalogado_id=:b"
        ), {"t": tenant_id, "a": a, "b": b})
        conn.commit()
        return a, b


def test_lista_conversiones(tenant_id):
    r = client.get("/api/v1/conversiones", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_crear_conversion(tenant_id, two_productos):
    cat_id, no_cat_id = two_productos
    payload = {
        "producto_catalogado_id": cat_id,
        "producto_no_catalogado_id": no_cat_id,
        "factor": 1.05,
        "merma_pct": 0.05,
        "prioridad": 5,
    }
    r = client.post("/api/v1/conversiones", json=payload, headers={"x-tenant-id": tenant_id})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["producto_catalogado_id"] == cat_id
    assert float(body["factor"]) == 1.05


def test_conversion_duplicada_409(tenant_id, two_productos):
    cat_id, no_cat_id = two_productos
    payload = {
        "producto_catalogado_id": cat_id,
        "producto_no_catalogado_id": no_cat_id,
        "factor": 1.0,
    }
    # primera vez puede ser 201 o 409 (si ya existe del test anterior)
    r1 = client.post("/api/v1/conversiones", json=payload, headers={"x-tenant-id": tenant_id})
    assert r1.status_code in (201, 409)
    # segunda siempre 409
    r2 = client.post("/api/v1/conversiones", json=payload, headers={"x-tenant-id": tenant_id})
    assert r2.status_code == 409


def test_conversion_mismo_producto_400(tenant_id, two_productos):
    cat_id, _ = two_productos
    payload = {
        "producto_catalogado_id": cat_id,
        "producto_no_catalogado_id": cat_id,
        "factor": 1.0,
    }
    r = client.post("/api/v1/conversiones", json=payload, headers={"x-tenant-id": tenant_id})
    assert r.status_code == 400


def test_conversion_producto_inexistente_404(tenant_id):
    payload = {
        "producto_catalogado_id": "00000000-0000-0000-0000-000000000000",
        "producto_no_catalogado_id": "00000000-0000-0000-0000-000000000001",
        "factor": 1.0,
    }
    r = client.post("/api/v1/conversiones", json=payload, headers={"x-tenant-id": tenant_id})
    assert r.status_code == 404


def test_conversiones_disponibles_para_producto(tenant_id, two_productos):
    cat_id, _ = two_productos
    r = client.get(
        f"/api/v1/conversiones/producto/{cat_id}/conversiones-disponibles",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_filter_listado_por_catalogado(tenant_id, two_productos):
    cat_id, _ = two_productos
    r = client.get(
        f"/api/v1/conversiones?catalogado_id={cat_id}",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
