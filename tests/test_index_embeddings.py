"""
Pruebas de integración del orquestador de indexación (src/index_embeddings.py).

Inyectan un **store falso** (mismo contrato `upsert`/`count` que ChromaVectorStore)
para validar el flujo `*.embeddings.jsonl -> upsert` SIN depender de chromadb.
Cubre RF-06.
"""

import json
from pathlib import Path

from src.config import Config
from src.index_embeddings import load_embedding_records, run


class FakeStore:
    """Store en memoria con el mismo contrato que ChromaVectorStore."""

    def __init__(self):
        self.points = {}  # id -> (embedding, metadata, document)

    def upsert(self, payload):
        for i, _id in enumerate(payload["ids"]):
            self.points[_id] = (
                payload["embeddings"][i],
                payload["metadatas"][i],
                payload["documents"][i],
            )

    def count(self):
        return len(self.points)


def _config(processed: Path) -> Config:
    cfg = Config(processed_path=str(processed))
    cfg.validate()
    return cfg


def _write_embeddings(path: Path, ids):
    with path.open("w", encoding="utf-8") as fh:
        for cid in ids:
            rec = {
                "chunk_id": cid,
                "embedding": [0.1, 0.2, 0.3],
                "embedding_model": "m",
                "embedding_dim": 3,
                "source_file": "haproxy_sample.log",
                "line_start": 1, "line_end": 5,
                "ts_start": "2026-02-10T14:00:00+00:00",
                "ts_end": "2026-02-10T14:00:05+00:00",
                "severities": {"info": 5},
            }
            fh.write(json.dumps(rec) + "\n")


def test_run_indexa_con_store_falso(tmp_path):
    _write_embeddings(tmp_path / "haproxy_sample.embeddings.jsonl", ["a", "b"])
    _write_embeddings(tmp_path / "iis_sample.embeddings.jsonl", ["c"])

    store = FakeStore()
    code = run(_config(tmp_path), store=store)
    assert code == 0
    assert store.count() == 3  # a, b, c


def test_run_upsert_es_idempotente(tmp_path):
    _write_embeddings(tmp_path / "x.embeddings.jsonl", ["a", "b"])
    store = FakeStore()
    run(_config(tmp_path), store=store)
    run(_config(tmp_path), store=store)  # reindexar no duplica (upsert por id)
    assert store.count() == 2


def test_run_sin_archivos_devuelve_error(tmp_path):
    assert run(_config(tmp_path), store=FakeStore()) == 1


def test_load_embedding_records(tmp_path):
    p = tmp_path / "x.embeddings.jsonl"
    p.write_text('{"chunk_id":"a"}\n\n{"chunk_id":"b"}\n', encoding="utf-8")
    assert [r["chunk_id"] for r in load_embedding_records(p)] == ["a", "b"]
