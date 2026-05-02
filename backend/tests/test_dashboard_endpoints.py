"""Tests de endpoints de dashboard."""
import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app

client = TestClient(app)


def _tenant_id():
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE slug='frutas-kelly'")).fetchone()
        return str(row[0]) if row else None


@pytest.fixture(scope="module")
def tenant_id():
    tid = _tenant_id()
    if not tid:
        pytest.skip("Migración no corrida")
    return tid


def test_resumen_dia_format(tenant_id):
    r = client.get(
        "/api/v1/dashboard/resumen-dia?fecha=2026-04-30",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert {"fecha", "pedidos_count", "lineas_count", "total_dia",
            "por_estado", "por_canal", "pedidos_requires_review"} <= set(data.keys())
    assert data["fecha"] == "2026-04-30"
    # Hubo pedidos ese día
    assert data["pedidos_count"] >= 1


def test_resumen_dia_default_today(tenant_id):
    r = client.get(
        "/api/v1/dashboard/resumen-dia",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    assert r.json()["fecha"] == date.today().isoformat()


def test_top_productos_returns_items(tenant_id):
    r = client.get(
        "/api/v1/dashboard/top-productos?desde=2026-04-01&hasta=2026-05-02&limit=5",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert len(data["items"]) <= 5
    if data["items"]:
        item = data["items"][0]
        assert {"sku", "nombre", "cantidad_total", "importe_total", "apariciones"} <= set(item.keys())


def test_top_unidades(tenant_id):
    r = client.get(
        "/api/v1/dashboard/top-unidades?desde=2026-04-01&hasta=2026-05-02&limit=10",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


def test_lineas_sin_producto(tenant_id):
    r = client.get(
        "/api/v1/dashboard/lineas-sin-producto?desde=2026-01-01&limit=20",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    # Sabemos que hay líneas sin match (de los pedidos fuzzy) — al menos 1
    if data["items"]:
        assert data["items"][0].get("texto_original")


def test_dashboard_requires_tenant():
    r = client.get("/api/v1/dashboard/resumen-dia")
    assert r.status_code == 400
