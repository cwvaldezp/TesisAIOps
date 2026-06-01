"""
Pruebas del orquestador del Embedder (src/embed_chunks.py) — RF-05.

Solo prueban el I/O (carga de chunks y escritura de registros), que NO requiere
el modelo real. El flujo completo `run()` (que carga el modelo) se valida de
forma manual/demostrativa para no descargar el modelo en las pruebas.
"""

import json
from pathlib import Path

from src.embed_chunks import load_chunks, write_records


def test_load_chunks_ignora_lineas_vacias(tmp_path):
    p = tmp_path / "x.chunks.jsonl"
    p.write_text('{"chunk_id":"c-0"}\n\n{"chunk_id":"c-1"}\n', encoding="utf-8")
    chunks = load_chunks(p)
    assert [c["chunk_id"] for c in chunks] == ["c-0", "c-1"]


def test_write_records_genera_jsonl(tmp_path):
    recs = [
        {"chunk_id": "c-0", "embedding": [0.1, 0.2], "embedding_dim": 2},
        {"chunk_id": "c-1", "embedding": [0.3, 0.4], "embedding_dim": 2},
    ]
    out = tmp_path / "x.embeddings.jsonl"
    write_records(recs, out)

    lineas = out.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 2
    assert json.loads(lineas[0])["chunk_id"] == "c-0"


def test_load_chunks_json_invalido(tmp_path):
    p = tmp_path / "bad.chunks.jsonl"
    p.write_text("{no es json}\n", encoding="utf-8")
    try:
        load_chunks(p)
        assert False, "debería haber lanzado ValueError"
    except ValueError:
        pass
