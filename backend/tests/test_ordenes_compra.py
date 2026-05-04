"""Tests para ordenes de compra (Sprint 7)."""
import os
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
def proveedor_id(tenant_id):
    """Crea un proveedor de prueba si no existe."""
    engine = create_engine(os.environ["DATABASE_URL"])
    import uuid
    with engine.connect() as conn:
        existing = conn.execute(text(
            "SELECT id FROM proveedores WHERE tenant_id=:t LIMIT 1"
        ), {"t": tenant_id}).fetchone()
        if existing:
            return str(existing[0])
        # crear uno nuevo
        new_id = str(uuid.uuid4())
        conn.execute(text(
            "INSERT INTO proveedores (id, tenant_id, codigo, nombre, activo) "
            "VALUES (:id, :t, :code, :name, true)"
        ), {
            "id": new_id, "t": tenant_id,
            "code": "TEST-001", "name": "Proveedor Test",
        })
        conn.commit()
        return new_id


@pytest.fixture(scope="module")
def producto_id(tenant_id):
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT id FROM productos WHERE tenant_id=:t LIMIT 1"
        ), {"t": tenant_id}).fetchone()
        return str(row[0]) if row else None


def test_lista_ordenes_compra(tenant_id):
    r = client.get("/api/v1/ordenes-compra", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_crear_orden_compra(tenant_id, proveedor_id, producto_id):
    r = client.post(
        "/api/v1/ordenes-compra",
        json={
            "proveedor_id": proveedor_id,
            "fecha": "2026-05-04",
            "estado": "BORRADOR",
            "lineas": [
                {
                    "producto_id": producto_id,
                    "cantidad_solicitada": 10,
                    "presentacion": "KILO",
                    "precio_unitario": 25,
                    "importe": 250,
                }
            ],
        },
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["folio"].startswith("OC-")
    assert body["estado"] == "BORRADOR"
    assert len(body["lineas"]) == 1
    assert float(body["total_estimado"]) == 250.0


def test_transition_orden_compra(tenant_id, proveedor_id, producto_id):
    create = client.post(
        "/api/v1/ordenes-compra",
        json={
            "proveedor_id": proveedor_id,
            "fecha": "2026-05-04",
            "lineas": [
                {
                    "producto_id": producto_id,
                    "cantidad_solicitada": 5,
                    "precio_unitario": 10,
                    "importe": 50,
                }
            ],
        },
        headers={"x-tenant-id": tenant_id},
    )
    oc_id = create.json()["id"]

    # BORRADOR -> ENVIADA valido
    r = client.post(
        f"/api/v1/ordenes-compra/{oc_id}/transition",
        json={"nuevo_estado": "ENVIADA"},
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "ENVIADA"

    # ENVIADA -> ENTREGADA invalido (no esta en transitions)
    r = client.post(
        f"/api/v1/ordenes-compra/{oc_id}/transition",
        json={"nuevo_estado": "ENTREGADA"},
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 400


def test_proveedor_inexistente(tenant_id, producto_id):
    r = client.post(
        "/api/v1/ordenes-compra",
        json={
            "proveedor_id": "00000000-0000-0000-0000-000000000000",
            "fecha": "2026-05-04",
            "lineas": [{
                "producto_id": producto_id,
                "cantidad_solicitada": 1,
                "precio_unitario": 1,
                "importe": 1,
            }],
        },
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 404
