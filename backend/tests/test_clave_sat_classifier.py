"""Tests del clasificador de clave SAT (offline cuando no hay API key)."""
import pytest

from app.services.clave_sat_classifier import (
    ClaveSatClassifier, ClassifierConfigError, _build_user_prompt, CLAVES_FYV,
)


def test_classifier_not_configured_without_key():
    c = ClaveSatClassifier(api_key=None)
    assert c.configured is False
    with pytest.raises(ClassifierConfigError):
        c.classify("Mango")


def test_classifier_configured_with_key():
    c = ClaveSatClassifier(api_key="sk-test")
    assert c.configured is True


def test_user_prompt_contains_inputs_and_claves():
    prompt = _build_user_prompt("Mango Manila", "Fruta tropical", "Frutas")
    assert "Mango Manila" in prompt
    assert "Fruta tropical" in prompt
    assert "Frutas" in prompt
    assert "50202301" in prompt
    assert "JSON" in prompt


def test_claves_fyv_has_generic_fallback():
    claves = {c for c, _ in CLAVES_FYV}
    assert "50202301" in claves  # genérico FyV


def test_endpoint_returns_503_when_no_key(monkeypatch):
    """Si ANTHROPIC_API_KEY no está, /classify-clave-sat devuelve 503."""
    import os
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from app.main import app

    if "DATABASE_URL" not in os.environ:
        pytest.skip("DATABASE_URL no seteada")

    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        tid = conn.execute(text("SELECT id FROM tenants WHERE slug='frutas-kelly'")).scalar()
        pid = conn.execute(text(
            "SELECT id FROM productos WHERE tenant_id=:t LIMIT 1"
        ), {"t": tid}).scalar()
    if not (tid and pid):
        pytest.skip("No hay productos")

    monkeypatch.setattr("app.api.v1.productos.settings", type("S", (), {
        "ANTHROPIC_API_KEY": "",
    })())
    client = TestClient(app)
    r = client.post(
        f"/api/v1/productos/{pid}/classify-clave-sat",
        headers={"x-tenant-id": str(tid)},
    )
    assert r.status_code == 503
