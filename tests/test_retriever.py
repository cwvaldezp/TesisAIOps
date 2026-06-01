"""
Pruebas del Retriever (src/retriever.py) — ADR-014, Fase 3. Cubre RF-08.

NO usan chromadb ni el modelo real: inyectan `embed_fn` y `store` falsos. Validan
la conversión distancia→score, el orden/umbral, la reconstrucción de severidades,
los filtros de metadatos y el flujo `retrieve()`.
"""

import pytest

from src.retriever import (
    build_results,
    build_where,
    distance_to_score,
    reconstruct_severities,
    retrieve,
)


def test_distance_to_score_cosine_y_fallback():
    assert distance_to_score(0.0, "cosine") == 1.0     # idéntico
    assert distance_to_score(0.2, "cosine") == pytest.approx(0.8)
    # Otras métricas: monótono decreciente en (0,1].
    assert distance_to_score(0.0, "l2") == 1.0
    assert distance_to_score(1.0, "l2") == pytest.approx(0.5)


def test_reconstruct_severities_desde_planos():
    md = {"sev_info": 6, "sev_warning": 1, "sev_error": 4}
    assert reconstruct_severities(md) == {"info": 6, "warning": 1, "error": 4}
    # Las severidades en 0 no se incluyen.
    assert reconstruct_severities({"sev_info": 3, "sev_error": 0}) == {"info": 3}


def test_build_where_filtros():
    assert build_where() is None
    assert build_where(source="haproxy_sample.log") == {"source_file": "haproxy_sample.log"}
    assert build_where(severity="error") == {"sev_error": {"$gt": 0}}
    combo = build_where(source="x.log", severity="warning")
    assert combo == {"$and": [{"source_file": "x.log"}, {"sev_warning": {"$gt": 0}}]}


def test_build_where_severity_invalida():
    with pytest.raises(ValueError):
        build_where(severity="critical")


def _response():
    """Respuesta simulada de Chroma (plana, ya como la devuelve store.query)."""
    return {
        "ids": ["c-1", "c-0"],
        "distances": [0.40, 0.10],   # c-0 está más cerca (mejor)
        "documents": ["iis_sample.log:5-9", "haproxy_sample.log:1-11"],
        "metadatas": [
            {"source_file": "iis_sample.log", "line_start": 5, "line_end": 9,
             "ts_start": "2026-02-10T14:03:11+00:00", "ts_end": "2026-02-10T14:03:14+00:00",
             "sev_info": 0, "sev_warning": 0, "sev_error": 3},
            {"source_file": "haproxy_sample.log", "line_start": 1, "line_end": 11,
             "ts_start": "2026-02-10T14:00:01+00:00", "ts_end": "2026-02-10T14:03:20+00:00",
             "sev_info": 6, "sev_warning": 1, "sev_error": 4},
        ],
    }


def test_build_results_ordena_por_score_y_asigna_rank():
    res = build_results(_response(), metric="cosine")
    # c-0 (distance 0.10 -> score 0.90) debe quedar primero pese a venir 2º.
    assert [r["chunk_id"] for r in res] == ["c-0", "c-1"]
    assert res[0]["rank"] == 1 and res[0]["score"] == 0.9
    assert res[0]["line_start"] == 1 and res[0]["line_end"] == 11
    assert res[0]["severities"] == {"info": 6, "warning": 1, "error": 4}
    assert res[1]["severities"] == {"error": 3}


def test_build_results_aplica_umbral():
    # score_threshold 0.7 descarta c-1 (score 0.60), conserva c-0 (0.90).
    res = build_results(_response(), metric="cosine", score_threshold=0.7)
    assert [r["chunk_id"] for r in res] == ["c-0"]


class FakeStore:
    def __init__(self, response):
        self.response = response
        self.last_args = None

    def query(self, embedding, top_k, where=None):
        self.last_args = (embedding, top_k, where)
        return self.response


def fake_embed(textos):
    return [[0.1, 0.2, 0.3] for _ in textos]


def test_retrieve_flujo_completo():
    store = FakeStore(_response())
    res = retrieve("errores 503 backend down", embed_fn=fake_embed, store=store,
                   top_k=5, metric="cosine")
    assert [r["chunk_id"] for r in res] == ["c-0", "c-1"]
    # Se pasó el vector embebido y el top_k al store.
    assert store.last_args[1] == 5


def test_retrieve_consulta_vacia():
    with pytest.raises(ValueError):
        retrieve("   ", embed_fn=fake_embed, store=FakeStore(_response()))


def test_retrieve_pasa_filtro_where():
    store = FakeStore({"ids": [], "distances": [], "documents": [], "metadatas": []})
    retrieve("x", embed_fn=fake_embed, store=store, where={"source_file": "a.log"})
    assert store.last_args[2] == {"source_file": "a.log"}
