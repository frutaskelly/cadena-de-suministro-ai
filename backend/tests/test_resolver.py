"""Tests del endpoint /productos/resolve y de la búsqueda con sinónimos."""
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


@pytest.fixture(scope="module")
def tenant_id():
    tid = _tenant_id()
    if not tid:
        pytest.skip("Migración no corrida")
    return tid


def test_resolve_via_synonym_tomate(tenant_id):
    """'tomate' está como sinónimo de JITOMATE SALADET."""
    r = client.get(
        "/api/v1/productos/resolve?alimento=tomate",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["matched"] is True
    assert "jitomate" in data["producto"]["nombre"].lower()


def test_resolve_via_synonym_jalapeno(tenant_id):
    """'jalapeno' está como sinónimo de CHILE CUARESMEÑO."""
    r = client.get(
        "/api/v1/productos/resolve?alimento=jalapeno",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["matched"] is True
    assert "chile" in data["producto"]["nombre"].lower()


def test_resolve_via_substring(tenant_id):
    r = client.get(
        "/api/v1/productos/resolve?alimento=manzana",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    if data["matched"]:
        assert "manzana" in data["producto"]["nombre"].lower()


def test_resolve_unmatched(tenant_id):
    r = client.get(
        "/api/v1/productos/resolve?alimento=producto_inventado_xyz_abc_zzzzzz",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["matched"] is False
    assert data["producto"] is None


def test_search_with_synonym_in_q(tenant_id):
    """Verifica que /productos?q=tomate también encuentre por sinónimo."""
    r = client.get(
        "/api/v1/productos?q=tomate",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    productos = r.json()
    assert len(productos) > 0
    # Al menos uno debe ser JITOMATE SALADET (por sinónimo)
    nombres = [p["nombre"].lower() for p in productos]
    assert any("jitomate" in n for n in nombres)
