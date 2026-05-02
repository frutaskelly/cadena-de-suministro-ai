"""Tests del cliente Facturama (offline — sin credenciales)."""
import pytest

from app.services.facturama import (
    FacturamaClient, FacturamaCredentials,
    FacturamaConfigError, FacturamaError,
)


class FakeSettings:
    def __init__(self, **kw):
        self.FACTURAMA_USER = kw.get("user", "")
        self.FACTURAMA_PASSWORD = kw.get("password", "")
        self.FACTURAMA_BASE_URL = kw.get("base_url", "https://apisandbox.facturama.mx")


def test_credentials_from_settings_returns_none_without_creds():
    s = FakeSettings(user="", password="")
    assert FacturamaCredentials.from_settings(s) is None


def test_credentials_from_settings_with_creds():
    s = FakeSettings(user="u", password="p")
    creds = FacturamaCredentials.from_settings(s)
    assert creds is not None
    assert creds.user == "u"


def test_client_not_configured_raises_on_call():
    client = FacturamaClient(creds=None)
    assert client.configured is False
    with pytest.raises(FacturamaConfigError):
        client.create_cfdi({})


def test_client_configured_property():
    creds = FacturamaCredentials(user="u", password="p")
    client = FacturamaClient(creds=creds)
    assert client.configured is True


def test_client_from_settings_factory():
    s = FakeSettings(user="u", password="p")
    client = FacturamaClient.from_settings(s)
    assert client.configured is True
