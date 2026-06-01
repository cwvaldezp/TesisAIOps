"""
Pruebas del parser HAProxy (src/parsers/haproxy.py) — cubre RF-01.

Verifican: extracción de campos de una línea válida, manejo del caso 503
sin servidor (<NOSRV>, timers -1), líneas vacías ('skip') y corruptas ('error').
"""

from src.parsers import STATUS_ERROR, STATUS_OK, STATUS_SKIP
from src.parsers.haproxy import HAProxyParser

# Línea HTTP de HAProxy estándar (200 OK).
LINE_OK = (
    "Feb 10 14:00:01 lb01 haproxy[2451]: 203.0.113.10:51234 "
    "[10/Feb/2026:14:00:01.123] fe_http be_web/web01 0/0/1/12/13 200 2456 "
    '- - ---- 12/12/3/1/0 0/0 "GET /index.html HTTP/1.1"'
)

# Línea de incidente: backend sin servidor disponible -> 503, timers en -1.
LINE_503 = (
    "Feb 10 14:03:11 lb01 haproxy[2451]: 203.0.113.15:51288 "
    "[10/Feb/2026:14:03:11.005] fe_http be_api/<NOSRV> 0/-1/-1/-1/0 503 213 "
    '- - SC-- 20/20/9/0/0 0/0 "GET /api/v1/orders HTTP/1.1"'
)


def test_haproxy_linea_valida():
    parser = HAProxyParser(timezone="UTC")
    status, ev = parser.parse_line(LINE_OK, line_number=1, source_file="haproxy_sample.log")

    assert status == STATUS_OK
    assert ev["source"] == "haproxy"
    assert ev["client_ip"] == "203.0.113.10"
    assert ev["method"] == "GET"
    assert ev["path"] == "/index.html"
    assert ev["status_code"] == 200
    assert ev["bytes"] == 2456
    assert ev["duration_ms"] == 13          # Tt
    assert ev["backend"] == "be_web/web01"
    assert ev["severity"] == "info"
    assert ev["timestamp"] == "2026-02-10T14:00:01+00:00"
    assert ev["line_number"] == 1


def test_haproxy_503_sin_servidor():
    parser = HAProxyParser()
    status, ev = parser.parse_line(LINE_503, line_number=6, source_file="haproxy_sample.log")

    assert status == STATUS_OK
    assert ev["status_code"] == 503
    assert ev["severity"] == "error"
    assert ev["backend"] == "be_api/<NOSRV>"
    # Tt es 0 aquí; los timers intermedios -1 no deben romper el parseo.
    assert ev["duration_ms"] == 0


def test_haproxy_linea_vacia_es_skip():
    parser = HAProxyParser()
    status, ev = parser.parse_line("   ", line_number=99, source_file="x.log")
    assert status == STATUS_SKIP
    assert ev is None


def test_haproxy_linea_corrupta_es_error():
    parser = HAProxyParser()
    status, ev = parser.parse_line(
        "ESTA-LINEA-ESTA-CORRUPTA", line_number=12, source_file="x.log"
    )
    assert status == STATUS_ERROR
    assert ev is None
