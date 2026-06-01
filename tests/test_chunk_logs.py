"""
Pruebas de integración del orquestador del Chunker (src/chunk_logs.py) — RF-04.

Demuestran el entregable de la Fase 2B: `*.events.jsonl -> Chunker -> *.chunks.jsonl`,
usando un archivo de eventos temporal y verificando la salida JSONL.
"""

import json
from pathlib import Path

from src.chunk_logs import load_events, run
from src.config import Config


def _config(processed: Path, size=4, overlap=1) -> Config:
    cfg = Config(
        processed_path=str(processed),
        chunk_strategy="by_events",
        chunk_size=size,
        chunk_overlap=overlap,
    )
    cfg.validate()
    return cfg


def _write_events(path: Path, n: int) -> None:
    """Escribe n eventos mínimos como JSONL en `path`."""
    with path.open("w", encoding="utf-8") as fh:
        for i in range(1, n + 1):
            ev = {
                "timestamp": "2026-02-10T14:00:00+00:00",
                "source": "haproxy",
                "severity": "info",
                "client_ip": None, "method": "GET", "path": "/x",
                "status_code": 200, "bytes": 1, "duration_ms": 1,
                "backend": "be/web", "source_file": "demo.log",
                "line_number": i, "raw": f"linea {i}",
            }
            fh.write(json.dumps(ev) + "\n")


def test_run_genera_chunks_jsonl(tmp_path):
    # Prepara un archivo de eventos como el que produce el parser.
    _write_events(tmp_path / "demo.events.jsonl", 10)

    code = run(_config(tmp_path, size=4, overlap=1))
    assert code == 0

    out = tmp_path / "demo.chunks.jsonl"
    assert out.exists()

    lineas = out.read_text(encoding="utf-8").splitlines()
    # 10 eventos, size=4, overlap=1 (paso 3) -> 3 chunks.
    assert len(lineas) == 3

    primer = json.loads(lineas[0])
    for clave in ("chunk_id", "source_file", "line_start", "line_end", "n_events", "text"):
        assert clave in primer
    assert primer["chunk_id"] == "demo-0"


def test_run_sin_archivos_devuelve_error(tmp_path):
    # processed_path existe pero no hay *.events.jsonl.
    assert run(_config(tmp_path)) == 1


def test_load_events_ignora_lineas_vacias(tmp_path):
    p = tmp_path / "x.events.jsonl"
    p.write_text('{"a":1}\n\n{"b":2}\n', encoding="utf-8")
    assert load_events(p) == [{"a": 1}, {"b": 2}]
