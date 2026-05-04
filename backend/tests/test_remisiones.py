"""Tests para remisiones (Sprint 7)."""
import os
from decimal import Decimal

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
def existing_pedido_id(tenant_id):
    """Toma un pedido existente para crear remisión."""
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT id FROM pedidos WHERE tenant_id=:t AND estado='CONFIRMADO' LIMIT 1"
        ), {"t": tenant_id}).fetchone()
        if not row:
            pytest.skip("No hay pedidos CONFIRMADO disponibles")
        return str(row[0])


def test_lista_remisiones_vacia_o_con_datos(tenant_id):
    r = client.get("/api/v1/remisiones", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_inventario_triple_estado_endpoint(tenant_id):
    r = client.get("/api/v1/remisiones/inventario/triple-estado",
                   headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # Sin lotes existentes regresa lista vacia, lo cual es OK


def test_crear_remision_desde_pedido(tenant_id, existing_pedido_id):
    r = client.post(
        f"/api/v1/remisiones/from-pedido/{existing_pedido_id}",
        json={"notas": "Test creacion desde pedido"},
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["pedido_id"] == existing_pedido_id
    assert body["folio"].startswith("R-")
    assert body["lineas_count"] >= 0


def test_get_remision_individual(tenant_id, existing_pedido_id):
    # crear primero
    create = client.post(
        f"/api/v1/remisiones/from-pedido/{existing_pedido_id}",
        json={},
        headers={"x-tenant-id": tenant_id},
    )
    rem_id = create.json()["remision_id"]

    r = client.get(f"/api/v1/remisiones/{rem_id}", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    assert r.json()["id"] == rem_id


def test_transition_remision_invalida(tenant_id, existing_pedido_id):
    create = client.post(
        f"/api/v1/remisiones/from-pedido/{existing_pedido_id}",
        json={},
        headers={"x-tenant-id": tenant_id},
    )
    rem_id = create.json()["remision_id"]

    # GENERADA -> CONFIRMADA es invalida (no esta en allowed)
    r = client.post(
        f"/api/v1/remisiones/{rem_id}/transition",
        json={"nuevo_estado": "CONFIRMADA"},
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 400
    assert "invalida" in r.json()["detail"].lower()


def test_transition_remision_valida(tenant_id, existing_pedido_id):
    create = client.post(
        f"/api/v1/remisiones/from-pedido/{existing_pedido_id}",
        json={},
        headers={"x-tenant-id": tenant_id},
    )
    rem_id = create.json()["remision_id"]

    # GENERADA -> EN_TRANSITO valido
    r = client.post(
        f"/api/v1/remisiones/{rem_id}/transition",
        json={"nuevo_estado": "EN_TRANSITO"},
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "EN_TRANSITO"


def test_create_remision_from_pedido_inexistente(tenant_id):
    r = client.post(
        "/api/v1/remisiones/from-pedido/00000000-0000-0000-0000-000000000000",
        json={},
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 400
