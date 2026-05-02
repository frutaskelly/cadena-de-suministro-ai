"""Smoke tests: el stack completo arranca y responde con los datos migrados."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

# Load .env before importing app
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.main import app  # noqa: E402

client = TestClient(app)


def _get_tenant_id():
    """Encuentra el tenant Frutas Kelly por slug."""
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE slug='frutas-kelly'")).fetchone()
        return str(row[0]) if row else None


@pytest.fixture(scope="module")
def tenant_id():
    tid = _get_tenant_id()
    if not tid:
        pytest.skip("Migración no corrida; corre `python ../scripts/migrate_frutas_kelly.py` primero")
    return tid


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root():
    r = client.get("/")
    assert r.status_code == 200


def test_tenants_list():
    r = client.get("/api/v1/tenants")
    assert r.status_code == 200
    data = r.json()
    assert any(t["slug"] == "frutas-kelly" for t in data)


def test_clientes_requires_tenant_header():
    r = client.get("/api/v1/clientes")
    assert r.status_code == 400


def test_clientes_listing(tenant_id):
    r = client.get("/api/v1/clientes", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    codigos = {c["codigo"] for c in data}
    assert "EHMO" in codigos
    assert "SURENA" in codigos


def test_clientes_search(tenant_id):
    r = client.get("/api/v1/clientes?q=ehmo", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    assert any(c["codigo"] == "EHMO" for c in r.json())


def test_productos_count_and_search(tenant_id):
    r = client.get("/api/v1/productos?limit=200", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    productos = r.json()
    assert len(productos) >= 100, f"expected >=100 productos, got {len(productos)}"

    r2 = client.get("/api/v1/productos?q=mango", headers={"x-tenant-id": tenant_id})
    assert r2.status_code == 200
    nombres = [p["nombre"].lower() for p in r2.json()]
    assert any("mango" in n for n in nombres)


def test_listas_precios(tenant_id):
    r = client.get("/api/v1/listas-precios", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    listas = r.json()
    codigos = {l["codigo"] for l in listas}
    assert "EHMO" in codigos
    assert "SURENA" in codigos


def test_contratos(tenant_id):
    r = client.get("/api/v1/contratos", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    contratos = r.json()
    contratantes = {c["contratante"] for c in contratos}
    assert "EHMO" in contratantes
    assert "SUREÑA" in contratantes


def test_unidades_de_contrato(tenant_id):
    contratos = client.get(
        "/api/v1/contratos", headers={"x-tenant-id": tenant_id}
    ).json()
    ehmo = next(c for c in contratos if c["contratante"] == "EHMO")
    r = client.get(
        f"/api/v1/unidades-entrega/by-contrato/{ehmo['id']}",
        headers={"x-tenant-id": tenant_id},
    )
    assert r.status_code == 200
    unidades = r.json()
    assert len(unidades) == 21, f"EHMO debería tener 21 hospitales, got {len(unidades)}"
    nombres = [u["nombre"] for u in unidades]
    assert any("Chiapa de Corzo" in n for n in nombres)


def test_pedidos_listing(tenant_id):
    r = client.get("/api/v1/pedidos", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    pedidos = r.json()
    assert len(pedidos) >= 10, f"esperaba >=10 pedidos migrados, got {len(pedidos)}"


def test_pedido_con_lineas(tenant_id):
    pedidos = client.get(
        "/api/v1/pedidos?fecha=2026-04-30&limit=1",
        headers={"x-tenant-id": tenant_id},
    ).json()
    if not pedidos:
        pytest.skip("No hay pedidos del 2026-04-30")
    pid = pedidos[0]["id"]
    r = client.get(f"/api/v1/pedidos/{pid}", headers={"x-tenant-id": tenant_id})
    assert r.status_code == 200
    p = r.json()
    assert len(p["lineas"]) > 0
    assert p["total"] is not None
