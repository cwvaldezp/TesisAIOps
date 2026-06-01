"""
Pruebas del vector store (src/vector_store.py) — ADR-013, Fase 2D. Cubre RF-06.

NO usan chromadb: prueban la LÓGICA PURA de transformación a payload de Chroma
(aplanado de metadatos, documento de cita, ids/embeddings paralelos), que es lo
que garantiza la citabilidad y la compatibilidad con Chroma (solo escalares).
"""

from src.vector_store import (
    build_payload,
    to_chroma_document,
    to_chroma_metadata,
)


def _record(chunk_id="haproxy_sample-0"):
    return {
        "chunk_id": chunk_id,
        "embedding": [0.1, 0.2, 0.3],
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_dim": 3,
        "source_file": "haproxy_sample.log",
        "line_start": 1,
        "line_end": 11,
        "ts_start": "2026-02-10T14:00:01+00:00",
        "ts_end": "2026-02-10T14:03:20+00:00",
        "severities": {"info": 6, "warning": 1, "error": 4},
    }


def test_metadata_solo_escalares_y_aplana_severidades():
    md = to_chroma_metadata(_record())
    # Chroma solo admite escalares: ningún valor puede ser dict ni lista.
    for v in md.values():
        assert isinstance(v, (str, int, float, bool))
    # severities (dict) se aplana a contadores enteros.
    assert md["sev_info"] == 6
    assert md["sev_warning"] == 1
    assert md["sev_error"] == 4
    assert md["source_file"] == "haproxy_sample.log"
    assert md["line_start"] == 1 and md["line_end"] == 11


def test_metadata_sustituye_none_por_vacio():
    rec = _record()
    rec["ts_start"] = None
    rec["ts_end"] = None
    md = to_chroma_metadata(rec)
    assert md["ts_start"] == "" and md["ts_end"] == ""


def test_documento_es_referencia_de_cita():
    assert to_chroma_document(_record()) == "haproxy_sample.log:1-11"


def test_build_payload_listas_paralelas():
    recs = [_record("c-0"), _record("c-1")]
    payload = build_payload(recs)
    assert payload["ids"] == ["c-0", "c-1"]
    assert len(payload["embeddings"]) == 2
    assert len(payload["metadatas"]) == 2
    assert len(payload["documents"]) == 2
    assert payload["embeddings"][0] == [0.1, 0.2, 0.3]


def test_build_payload_vacio():
    payload = build_payload([])
    assert payload["ids"] == [] and payload["embeddings"] == []
