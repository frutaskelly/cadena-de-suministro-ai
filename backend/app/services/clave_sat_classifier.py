"""Clasificador de clave SAT (c_ClaveProdServ) usando Claude API.

Toma el nombre + descripción de un producto y devuelve la clave de 8 dígitos
del catálogo SAT más apropiada. Para Frutas Kelly el default genérico es
50202301 (Frutas y/o verduras frescas), pero hay claves más específicas para:
- 50261800 → frutas frescas específicas (manzana, pera, etc.)
- 50272000 → bulbos y tubérculos (cebolla, papa, ajo)
- 50404400 → frescas hierbas culinarias (hierbabuena, cilantro)

Usa prompt caching para reducir costo (la lista de claves cacheable es ~3KB).

Sin ANTHROPIC_API_KEY en .env, expone los métodos pero `classify()` levanta
ClassifierConfigError — útil para tests offline.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import json
import logging

log = logging.getLogger(__name__)


class ClassifierError(Exception):
    pass


class ClassifierConfigError(ClassifierError):
    pass


# Subset relevante para FyV de c_ClaveProdServ (CFDI 4.0).
# Si crece mucho, mover a tabla sat_productos_servicios y consultar de ahí.
CLAVES_FYV = [
    ("50202301", "Frutas y/o verduras frescas (genérico)"),
    ("50221200", "Verduras frescas"),
    ("50261800", "Frutas frescas"),
    ("50272000", "Verduras tipo bulbo y raíz frescas (cebolla, ajo, papa)"),
    ("50404400", "Hierbas culinarias frescas (hierbabuena, cilantro, perejil)"),
    ("50221300", "Hortalizas de hoja (espinaca, acelga, lechuga)"),
    ("50112000", "Carne y aves de corral fresca"),
    ("50130000", "Pescado fresco"),
    ("50131600", "Mariscos frescos"),
    ("50161500", "Productos lácteos frescos"),
    ("50180000", "Productos de panadería"),
    ("50190000", "Alimentos preparados y conservados"),
]


@dataclass
class ClaveSatResult:
    clave: str
    descripcion: str
    confidence: float  # 0..1
    rationale: str


SYSTEM_PROMPT = """Eres un clasificador del catálogo c_ClaveProdServ del SAT (México) para CFDI 4.0.

Dado el nombre/descripción de un producto en español, devuelves la clave SAT de 8 dígitos
más apropiada del subset proporcionado. Si dudas entre varias, prefiere la MÁS específica
sobre la genérica. Si ninguna aplica claramente, devuelve la genérica 01010101 con baja
confidence.

Devuelve JSON estricto con campos: clave (string 8 dígitos), descripcion (string),
confidence (float 0..1), rationale (string corto en español)."""


def _build_user_prompt(nombre: str, descripcion: Optional[str], categoria: Optional[str]) -> str:
    claves_block = "\n".join(f"  {c} = {d}" for c, d in CLAVES_FYV)
    return f"""Clasifica este producto:

Nombre: {nombre}
Descripción: {descripcion or '-'}
Categoría: {categoria or '-'}

Subset de claves disponibles:
{claves_block}

Responde SOLO con JSON: {{"clave": "...", "descripcion": "...", "confidence": 0.0, "rationale": "..."}}"""


class ClaveSatClassifier:
    def __init__(self, api_key: Optional[str], model: str = "claude-haiku-4-5-20251001"):
        self._api_key = api_key
        self._model = model
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _ensure_client(self):
        if self._client is None:
            if not self._api_key:
                raise ClassifierConfigError(
                    "ANTHROPIC_API_KEY no configurada en .env"
                )
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self._api_key)

    def classify(
        self,
        nombre: str,
        descripcion: Optional[str] = None,
        categoria: Optional[str] = None,
    ) -> ClaveSatResult:
        """Clasifica un producto. Levanta ClassifierError si falla."""
        self._ensure_client()
        prompt = _build_user_prompt(nombre, descripcion, categoria)
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=300,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            raise ClassifierError(f"Anthropic API failed: {e}") from e

        text = resp.content[0].text.strip()
        # Algunos modelos envuelven en ```json ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(l for l in lines if not l.strip().startswith("```"))
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise ClassifierError(f"Modelo devolvió no-JSON: {text[:200]}")

        clave = data.get("clave", "01010101")
        if not (clave and len(clave) == 8 and clave.isdigit()):
            raise ClassifierError(f"clave inválida: {clave!r}")
        return ClaveSatResult(
            clave=clave,
            descripcion=data.get("descripcion", ""),
            confidence=float(data.get("confidence", 0.0)),
            rationale=data.get("rationale", ""),
        )
