"""Tests del servicio de fuzzy matching."""
from uuid import uuid4

from app.services.fuzzy_match import normalize, best_match


def test_normalize_basics():
    assert normalize("Hospital Básico Comunitario") == "hospital basico comunitario"
    assert normalize("  Juan C. Corzo ") == "juan c corzo"
    assert normalize("Gónzalez") == "gonzalez"
    assert normalize("Las Casas") == normalize("las casas")
    assert normalize("") == ""
    assert normalize(None) == ""


def test_normalize_strips_punctuation_and_collapses_whitespace():
    assert normalize("a. b,  c") == "a b c"
    assert normalize("Hospital  General  -  Tonalá") == "hospital general tonala"


def test_best_match_exact_case_insensitive():
    cands = {
        uuid4(): "Hospital General Tapachula",
        uuid4(): "Hospital de la Mujer Comitán",
    }
    m = best_match("hospital general tapachula", cands)
    assert m is not None
    assert m.method == "exact"
    assert m.score == 100.0


def test_best_match_normalized_handles_accents_and_punct():
    target_id = uuid4()
    cands = {target_id: "Hospital General Dr. Juan C. Corzo Tonalá"}
    m = best_match("Hospital General Dr. Juan C Corzo Tonalá", cands)
    assert m is not None
    assert m.target_id == target_id
    assert m.method == "normalized"


def test_best_match_fuzzy_typo():
    target_id = uuid4()
    cands = {
        target_id: "Hospital Básico Comunitario Dr. Rafael Alfaro Gonzalez Pijijiapan",
        uuid4(): "Hospital Otro",
    }
    m = best_match("Hospital Basico Comunitario Dr Rafael Alfaro Gonzalez Pijijiapan", cands)
    assert m is not None
    assert m.target_id == target_id
    # 'normalized' ya que después de normalizar son iguales
    assert m.method in ("normalized", "fuzzy")


def test_best_match_below_threshold_returns_none():
    cands = {uuid4(): "Hospital General Tapachula"}
    m = best_match("Algo completamente distinto", cands, threshold=80.0)
    assert m is None


def test_best_match_empty_inputs():
    assert best_match("", {uuid4(): "x"}) is None
    assert best_match("hola", {}) is None
