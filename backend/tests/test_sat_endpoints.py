"""Tests de los endpoints read-only de catálogos SAT."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_formas_pago_seeded():
    r = client.get("/api/v1/sat/formas-pago")
    assert r.status_code == 200
    data = r.json()
    claves = {x["clave"] for x in data}
    assert "01" in claves  # Efectivo
    assert "99" in claves  # Por definir


def test_metodos_pago_pue_ppd():
    r = client.get("/api/v1/sat/metodos-pago")
    assert r.status_code == 200
    claves = {x["clave"] for x in r.json()}
    assert "PUE" in claves
    assert "PPD" in claves


def test_regimenes_filter_fisica():
    r = client.get("/api/v1/sat/regimenes?aplica=fisica")
    assert r.status_code == 200
    data = r.json()
    assert all(x["aplica_fisica"] == "Sí" for x in data)
    claves = {x["clave"] for x in data}
    assert "612" in claves  # Personas físicas con act. empresariales
    assert "626" in claves  # RESICO


def test_regimenes_filter_moral():
    r = client.get("/api/v1/sat/regimenes?aplica=moral")
    assert r.status_code == 200
    claves = {x["clave"] for x in r.json()}
    assert "601" in claves


def test_usos_cfdi_includes_g03():
    r = client.get("/api/v1/sat/usos-cfdi")
    assert r.status_code == 200
    claves = {x["clave"] for x in r.json()}
    assert "G03" in claves
    assert "S01" in claves


def test_unidades_search():
    r = client.get("/api/v1/sat/unidades?q=kilo")
    assert r.status_code == 200
    claves = {x["clave"] for x in r.json()}
    assert "KGM" in claves


def test_productos_servicios_search():
    r = client.get("/api/v1/sat/productos-servicios?q=fruta")
    assert r.status_code == 200
    data = r.json()
    claves = {x["clave"] for x in data}
    assert "50202301" in claves
