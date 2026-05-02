"""Fuzzy matching de nombres de unidades de entrega y productos.

Usa rapidfuzz para encontrar el mejor candidato cuando un nombre del input
no matchea exacto con la BD (por typos, acentos diferentes, capitalización,
puntuación, etc.).

Casos típicos resueltos:
- "Juan C Corzo" vs "Juan C. Corzo"
- "de Las Casas" vs "de las Casas"
- "Gónzalez" vs "Gonzalez"
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
import unicodedata

from rapidfuzz import fuzz, process


def normalize(s: str) -> str:
    """Lower + strip + ASCII fold + collapse whitespace + drop punctuation."""
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    out = []
    for ch in s:
        if ch.isalnum() or ch.isspace():
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


@dataclass
class FuzzyMatch:
    target_id: UUID
    target_name: str
    score: float          # 0..100
    method: str           # 'exact', 'normalized', 'fuzzy'


def best_match(
    query: str,
    candidates: dict[UUID, str],
    threshold: float = 85.0,
) -> Optional[FuzzyMatch]:
    """Encuentra el mejor match entre `candidates` (id → name) para `query`.

    Estrategia (en orden de prioridad):
      1. Exact match (case-insensitive, raw)
      2. Match exacto sobre normalize() — resuelve acentos/puntuación/case
      3. Fuzzy con rapidfuzz token_set_ratio — resuelve typos y orden
    """
    if not query or not candidates:
        return None

    q_lower = query.lower().strip()
    q_norm = normalize(query)

    norm_index: dict[str, list[tuple[UUID, str]]] = {}
    for cid, cname in candidates.items():
        norm_index.setdefault(normalize(cname), []).append((cid, cname))

    # 1. Exact (raw, case-insensitive)
    for cid, cname in candidates.items():
        if cname.lower().strip() == q_lower:
            return FuzzyMatch(cid, cname, 100.0, "exact")

    # 2. Normalized exact
    if q_norm in norm_index:
        cid, cname = norm_index[q_norm][0]
        return FuzzyMatch(cid, cname, 99.0, "normalized")

    # 3. Fuzzy
    norm_to_orig = {nk: vs[0] for nk, vs in norm_index.items()}
    result = process.extractOne(
        q_norm,
        list(norm_to_orig.keys()),
        scorer=fuzz.token_set_ratio,
        score_cutoff=threshold,
    )
    if result is None:
        return None
    matched_norm, score, _ = result
    cid, cname = norm_to_orig[matched_norm]
    return FuzzyMatch(cid, cname, float(score), "fuzzy")
