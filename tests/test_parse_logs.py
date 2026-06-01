"""
Pruebas de integración del orquestador (src/parse_logs.py) — cubre RF-01..RF-03.

Ejecutan el pipeline completo sobre los logs de ejemplo del repositorio y
verifican: autodetección de fuente, conteo de eventos, política on_parse_error
y la escritura de la salida normalizada.
"""

import json
from pathlib import Path

from src.config import Config
from src.parse_logs import detect_source, parse_file, run

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = REPO_ROOT / "data" / "logs"


def _base_config(processed: Path, on_parse_error: str = "skip") -> Config:
    """Config de prueba apuntando a los logs reales y a un dir temporal."""
    cfg = Config(
        logs_path=str(LOGS_DIR),
        file_pattern="*.log",
        encoding="utf-8",
        source_type="auto",
        on_parse_error=on_parse_error,
        timezone="UTC",
        processed_path=str(processed),
        parser_output_format="jsonl",
    )
    cfg.validate()
    return cfg


def test_detect_source_por_nombre_y_contenido():
    assert detect_source("haproxy_sample.log", []) == "haproxy"
    assert detect_source("iis_sample.log", []) == "iis"
    # Sin pista en el nombre, decide por contenido (directiva W3C).
    assert detect_source("acceso.log", ["#Fields: date time"]) == "iis"
    assert detect_source("acceso.log", ["algo no W3C"]) == "haproxy"


def test_parse_haproxy_sample_skip(tmp_path):
    cfg = _base_config(tmp_path, on_parse_error="skip")
    events, stats = parse_file(LOGS_DIR / "haproxy_sample.log", cfg, forced_source=None)

    assert stats["source"] == "haproxy"
    assert stats["ok"] == 11             # 11 líneas válidas
    assert stats["skipped_errors"] == 1  # 1 línea corrupta descartada
    assert len(events) == 11
    # Debe haber capturado el incidente: tres 503 de be_api/<NOSRV>.
    errores_503 = [e for e in events if e["status_code"] == 503]
    assert len(errores_503) == 3
    assert all(e["severity"] == "error" for e in errores_503)


def test_parse_haproxy_keep_conserva_corrupta(tmp_path):
    cfg = _base_config(tmp_path, on_parse_error="keep")
    events, stats = parse_file(LOGS_DIR / "haproxy_sample.log", cfg, forced_source=None)
    assert stats["kept_errors"] == 1
    # En modo keep, la línea corrupta se conserva con campos nulos pero con raw.
    assert len(events) == 12
    corrupta = events[-1]
    assert corrupta["status_code"] is None
    assert "CORRUPTA" in corrupta["raw"]


def test_parse_iis_sample(tmp_path):
    cfg = _base_config(tmp_path)
    events, stats = parse_file(LOGS_DIR / "iis_sample.log", cfg, forced_source=None)

    assert stats["source"] == "iis"
    assert stats["ok"] == 9  # 9 líneas de datos (las directivas '#' son skip)
    assert len(events) == 9
    assert all(e["source"] == "iis" for e in events)


def test_run_escribe_salida_jsonl(tmp_path):
    cfg = _base_config(tmp_path)
    code = run(cfg)
    assert code == 0

    out = tmp_path / "haproxy_sample.events.jsonl"
    assert out.exists()
    # Cada línea del JSONL debe ser un objeto JSON válido con las claves clave.
    primera = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    for clave in ("timestamp", "source", "severity", "status_code", "source_file", "line_number"):
        assert clave in primera
