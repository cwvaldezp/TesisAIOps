"""
Pruebas del Embedder (src/embedder.py) — ADR-012, Fase 2C. Cubre RF-05.

NO cargan el modelo real (sentence-transformers): inyectan una `encode_fn` falsa
y determinista. Así las pruebas son rápidas, offline y reproducibles, y validan
la LÓGICA (combinar vector + metadatos, esquema del registro, errores).
"""

import pytest

from src.embedder import (
    EMBEDDING_RECORD_FIELDS,
    build_embedding_record,
    embed_chunks,
)


def fake_encode(textos):
    """encode_fn falsa: vector determinista de dimensión 3 por cada texto.

    Usa [len(texto), nº de palabras, nº de líneas] para que dependa del contenido.
    """
    vectores = []
    for t in textos:
        vectores.append([float(len(t)), float(len(t.split())), float(t.count(chr(10)) + 1)])
    return vectores


def _chunk(chunk_id="c-0", text="hola mundo", **extra):
    base = {
        "chunk_id": chunk_id,
        "source_file": "haproxy_sample.log",
        "sources": ["haproxy"],
        "line_start": 1,
        "line_end": 5,
        "ts_start": "2026-02-10T14:00:00+00:00",
        "ts_end": "2026-02-10T14:05:00+00:00",
        "n_events": 5,
        "severities": {"info": 4, "error": 1},
        "event_lines": [1, 2, 3, 4, 5],
        "text": text,
    }
    base.update(extra)
    return base


def test_build_record_hereda_metadatos_y_dim():
    rec = build_embedding_record(_chunk(), [0.1, 0.2, 0.3], "fake-model")
    assert tuple(rec.keys()) == EMBEDDING_RECORD_FIELDS
    assert rec["embedding"] == [0.1, 0.2, 0.3]
    assert rec["embedding_dim"] == 3
    assert rec["embedding_model"] == "fake-model"
    # Metadatos de citabilidad/filtrado heredados del chunk.
    assert rec["chunk_id"] == "c-0"
    assert rec["source_file"] == "haproxy_sample.log"
    assert rec["line_start"] == 1 and rec["line_end"] == 5
    assert rec["severities"] == {"info": 4, "error": 1}


def test_embed_chunks_genera_un_registro_por_chunk():
    chunks = [_chunk("c-0", "uno"), _chunk("c-1", "dos palabras")]
    recs = embed_chunks(chunks, encode_fn=fake_encode, model_name="fake-model")
    assert len(recs) == 2
    assert [r["chunk_id"] for r in recs] == ["c-0", "c-1"]
    # El vector depende del texto (encode falsa determinista).
    assert recs[0]["embedding"][0] == 3.0          # len("uno")
    assert recs[1]["embedding"][1] == 2.0          # nº palabras de "dos palabras"


def test_embed_chunks_lista_vacia():
    assert embed_chunks([], encode_fn=fake_encode, model_name="m") == []


def test_embed_chunks_texto_vacio_no_rompe():
    recs = embed_chunks([_chunk("c-0", "")], encode_fn=fake_encode, model_name="m")
    assert recs[0]["embedding_dim"] == 3


def test_embed_chunks_detecta_desajuste_de_vectores():
    """Si encode_fn devuelve un nº de vectores != nº de chunks, debe fallar."""
    def bad_encode(textos):
        return [[0.0]]  # siempre un solo vector

    with pytest.raises(ValueError):
        embed_chunks([_chunk("a"), _chunk("b")], encode_fn=bad_encode, model_name="m")
