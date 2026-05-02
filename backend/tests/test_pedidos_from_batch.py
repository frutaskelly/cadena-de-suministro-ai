"""Tests del endpoint POST /pedidos/from-batch (y /from-excel-bd)."""
import os

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


def _cleanup_test_pedidos(tenant_id, fecha):
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as conn:
        conn.execute(text(
            "DELETE FROM lineas_pedido WHERE pedido_id IN "
            "(SELECT id FROM pedidos WHERE tenant_id=:t AND fecha_pedido=:f)"
        ), {"t": tenant_id, "f": fecha})
        conn.execute(text(
            "DELETE FROM pedidos WHERE tenant_id=:t AND fecha_pedido=:f"
        ), {"t": tenant_id, "f": fecha})


@pytest.fixture(scope="module")
def tenant_id():
    tid = _tenant_id()
    if not tid:
        pytest.skip("Migración no corrida")
    return tid


def test_from_batch_creates_pedido_with_sinonimos(tenant_id):
    fecha = "2026-12-30"  # fecha futura para no chocar con datos reales
    _cleanup_test_pedidos(tenant_id, fecha)

    payload = {
        "fecha": fecha,
        "canal": "EXCEL_BD",
        "rows": [
            {"unidad_nombre": "Hospital General de Huixtla", "alimento": "tomate", "cantidad": 10, "presentacion": "KILO"},
            {"unidad_nombre": "Hospital General de Huixtla", "alimento": "yerbabuena", "cantidad": 2, "presentacion": "KILO"},
            {"unidad_nombre": "Hospital General de Huixtla", "alimento": "Cebolla", "cantidad": 5, "presentacion": "KILO"},
        ],
    }
    try:
        r = client.post(
            "/api/v1/pedidos/from-batch",
            json=payload,
            headers={"x-tenant-id": tenant_id},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert len(data["pedidos_creados"]) == 1
        assert data["pedidos_creados"][0]["lineas_count"] == 3
        assert data["unidades_sin_match"] == []
    finally:
        _cleanup_test_pedidos(tenant_id, fecha)


def test_from_batch_fuzzy_matches_unidad(tenant_id):
    """Test fuzzy match 'Juan C Corzo' (sin punto) → 'Juan C. Corzo'."""
    fecha = "2026-12-31"
    _cleanup_test_pedidos(tenant_id, fecha)

    payload = {
        "fecha": fecha,
        "canal": "EXCEL_BD",
        "rows": [
            {"unidad_nombre": "Hospital General Dr. Juan C Corzo Tonalá", "alimento": "manzana", "cantidad": 5},
        ],
    }
    try:
        r = client.post(
            "/api/v1/pedidos/from-batch",
            json=payload,
            headers={"x-tenant-id": tenant_id},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert len(data["pedidos_creados"]) == 1
        assert data["unidades_sin_match"] == []
    finally:
        _cleanup_test_pedidos(tenant_id, fecha)


def test_from_batch_records_unmatched_lines(tenant_id):
    fecha = "2026-12-29"
    _cleanup_test_pedidos(tenant_id, fecha)

    payload = {
        "fecha": fecha,
        "canal": "EXCEL_BD",
        "rows": [
            {"unidad_nombre": "Hospital General de Huixtla", "alimento": "producto_completamente_inventado_xyz", "cantidad": 1},
        ],
    }
    try:
        r = client.post(
            "/api/v1/pedidos/from-batch",
            json=payload,
            headers={"x-tenant-id": tenant_id},
        )
        assert r.status_code == 201
        data = r.json()
        assert len(data["lineas_sin_match"]) == 1
        assert data["lineas_sin_match"][0]["alimento"] == "producto_completamente_inventado_xyz"
        # El pedido se crea aún sin producto matched
        assert len(data["pedidos_creados"]) == 1
        assert data["pedidos_creados"][0]["requires_review"] is True
    finally:
        _cleanup_test_pedidos(tenant_id, fecha)


def test_from_batch_records_unmatched_unidad(tenant_id):
    fecha = "2026-12-28"
    _cleanup_test_pedidos(tenant_id, fecha)

    payload = {
        "fecha": fecha,
        "canal": "EXCEL_BD",
        "rows": [
            {"unidad_nombre": "Hospital Inventado de Marte", "alimento": "tomate", "cantidad": 5},
        ],
    }
    try:
        r = client.post(
            "/api/v1/pedidos/from-batch",
            json=payload,
            headers={"x-tenant-id": tenant_id},
        )
        assert r.status_code == 201
        data = r.json()
        assert "Hospital Inventado de Marte" in data["unidades_sin_match"]
        assert len(data["pedidos_creados"]) == 0
    finally:
        _cleanup_test_pedidos(tenant_id, fecha)


def test_from_batch_skips_existing_without_force(tenant_id):
    fecha = "2026-12-27"
    _cleanup_test_pedidos(tenant_id, fecha)

    payload = {
        "fecha": fecha,
        "canal": "EXCEL_BD",
        "rows": [
            {"unidad_nombre": "Hospital General Tapachula", "alimento": "pera", "cantidad": 10},
        ],
    }
    try:
        # Primer call crea
        r1 = client.post(
            "/api/v1/pedidos/from-batch",
            json=payload,
            headers={"x-tenant-id": tenant_id},
        )
        assert r1.status_code == 201
        assert len(r1.json()["pedidos_creados"]) == 1

        # Segundo call sin force_overwrite skip
        r2 = client.post(
            "/api/v1/pedidos/from-batch",
            json=payload,
            headers={"x-tenant-id": tenant_id},
        )
        assert r2.status_code == 201
        d2 = r2.json()
        assert len(d2["pedidos_creados"]) == 0
        assert len(d2["pedidos_skipped"]) == 1
    finally:
        _cleanup_test_pedidos(tenant_id, fecha)


def test_from_excel_bd_alias_works(tenant_id):
    fecha = "2026-12-26"
    _cleanup_test_pedidos(tenant_id, fecha)

    payload = {
        "fecha": fecha,
        "canal": "FOO_IGNORED",  # debe ser sobreescrito a EXCEL_BD
        "rows": [
            {"unidad_nombre": "Hospital General Tapachula", "alimento": "tomate", "cantidad": 1},
        ],
    }
    try:
        r = client.post(
            "/api/v1/pedidos/from-excel-bd",
            json=payload,
            headers={"x-tenant-id": tenant_id},
        )
        assert r.status_code == 201
    finally:
        _cleanup_test_pedidos(tenant_id, fecha)
