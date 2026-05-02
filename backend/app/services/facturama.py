"""Cliente HTTP para Facturama (PAC para timbrado CFDI 4.0).

Esta capa es un thin wrapper que mapea nuestros modelos al payload de
Facturama API v1 (https://apisandbox.facturama.mx). Está stubbed: si no
hay credenciales en `.env` (FACTURAMA_USER / FACTURAMA_PASSWORD), expone
los métodos pero levanta `FacturamaConfigError` al ejecutar — útil para
tests offline y para correr CI sin secretos.

Formas de uso:
    client = FacturamaClient.from_settings(settings)
    if client.configured:
        result = client.create_cfdi(payload)
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

import logging
import httpx

log = logging.getLogger(__name__)


class FacturamaError(Exception):
    pass


class FacturamaConfigError(FacturamaError):
    pass


@dataclass
class FacturamaCredentials:
    user: str
    password: str
    base_url: str = "https://apisandbox.facturama.mx"  # sandbox por default

    @classmethod
    def from_settings(cls, settings) -> Optional["FacturamaCredentials"]:
        u = getattr(settings, "FACTURAMA_USER", None)
        p = getattr(settings, "FACTURAMA_PASSWORD", None)
        url = getattr(settings, "FACTURAMA_BASE_URL", "https://apisandbox.facturama.mx")
        if not u or not p:
            return None
        return cls(user=u, password=p, base_url=url.rstrip("/"))


class FacturamaClient:
    """Wrapper minimal para la API de Facturama.

    Solo cubre los endpoints que necesitamos en Sprint 4:
    - POST /api-lite/3/cfdis            : timbrado CFDI 4.0
    - DELETE /cfdi/{id}?type=issued&motive={motivo}&uuidReplacement={uuid}
    - GET /api-lite/cfdi/{id}/pdf       : descarga PDF
    - GET /cfdi/xml/issued/{id}         : descarga XML
    """

    def __init__(self, creds: Optional[FacturamaCredentials], timeout: float = 30.0):
        self._creds = creds
        self._timeout = timeout

    @classmethod
    def from_settings(cls, settings) -> "FacturamaClient":
        return cls(FacturamaCredentials.from_settings(settings))

    @property
    def configured(self) -> bool:
        return self._creds is not None

    def _client(self) -> httpx.Client:
        if not self._creds:
            raise FacturamaConfigError(
                "Facturama no configurado: define FACTURAMA_USER y FACTURAMA_PASSWORD en .env"
            )
        return httpx.Client(
            base_url=self._creds.base_url,
            auth=(self._creds.user, self._creds.password),
            timeout=self._timeout,
            headers={"Content-Type": "application/json"},
        )

    # ─── CFDI 4.0 ──────────────────────────────────────────────────────────

    def create_cfdi(self, payload: dict) -> dict:
        """Timbra CFDI. Devuelve el response de Facturama (incluye Id, Complement.TimbreFiscalDigital.UUID, etc.)."""
        with self._client() as c:
            r = c.post("/api-lite/3/cfdis", json=payload)
            if r.status_code >= 400:
                log.error(f"Facturama create_cfdi {r.status_code}: {r.text[:500]}")
                raise FacturamaError(f"create_cfdi failed: {r.status_code} {r.text}")
            return r.json()

    def cancel_cfdi(
        self, cfdi_id: str, motive: str, uuid_replacement: Optional[str] = None,
    ) -> dict:
        """Cancela. motive 01-04 (CFDI 4.0)."""
        params = {"type": "issued", "motive": motive}
        if uuid_replacement:
            params["uuidReplacement"] = uuid_replacement
        with self._client() as c:
            r = c.delete(f"/cfdi/{cfdi_id}", params=params)
            if r.status_code >= 400:
                raise FacturamaError(f"cancel_cfdi failed: {r.status_code} {r.text}")
            return r.json() if r.text else {}

    def download_pdf(self, cfdi_id: str) -> bytes:
        with self._client() as c:
            r = c.get(f"/api-lite/cfdi/{cfdi_id}/pdf")
            if r.status_code >= 400:
                raise FacturamaError(f"download_pdf failed: {r.status_code}")
            data = r.json()
            import base64
            return base64.b64decode(data.get("Content", ""))

    def download_xml(self, cfdi_id: str) -> bytes:
        with self._client() as c:
            r = c.get(f"/cfdi/xml/issued/{cfdi_id}")
            if r.status_code >= 400:
                raise FacturamaError(f"download_xml failed: {r.status_code}")
            return r.content
