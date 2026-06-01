"""
Pruebas del parser IIS W3C (src/parsers/iis.py) — cubre RF-02.

Verifican: lectura de columnas desde la directiva '#Fields:', parseo de una
línea de datos, combinación stem+query en `path`, y el error cuando llega una
línea de datos antes de conocer las columnas.
"""

from src.parsers import STATUS_ERROR, STATUS_OK, STATUS_SKIP
from src.parsers.iis import IISParser

FIELDS_LINE = (
    "#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port "
    "cs-username c-ip cs(User-Agent) sc-status sc-substatus sc-win32-status time-taken"
)
DATA_OK = (
    "2026-02-10 14:00:01 198.51.100.5 GET /home - 443 - 203.0.113.10 "
    "Mozilla/5.0+(Windows+NT+10.0) 200 0 0 35"
)
DATA_500_QUERY = (
    "2026-02-10 14:00:09 198.51.100.6 GET /api/products id=42 443 - 203.0.113.13 "
    "Mozilla/5.0+(iPhone) 500 0 2 1985"
)


def test_iis_directiva_fields_es_skip_y_define_columnas():
    parser = IISParser(timezone="UTC")
    status, ev = parser.parse_line(FIELDS_LINE, line_number=4, source_file="iis_sample.log")
    assert status == STATUS_SKIP
    assert ev is None
    assert parser.fields is not None and parser.fields[0] == "date"


def test_iis_linea_datos_valida():
    parser = IISParser(timezone="UTC")
    parser.parse_line(FIELDS_LINE, 4, "iis_sample.log")  # define columnas
    status, ev = parser.parse_line(DATA_OK, line_number=5, source_file="iis_sample.log")

    assert status == STATUS_OK
    assert ev["source"] == "iis"
    assert ev["client_ip"] == "203.0.113.10"
    assert ev["method"] == "GET"
    assert ev["path"] == "/home"
    assert ev["status_code"] == 200
    assert ev["duration_ms"] == 35          # time-taken en ms
    assert ev["backend"] is None            # IIS no expone backend
    assert ev["timestamp"] == "2026-02-10T14:00:01+00:00"


def test_iis_combina_stem_y_query_y_deriva_error():
    parser = IISParser()
    parser.parse_line(FIELDS_LINE, 4, "iis_sample.log")
    status, ev = parser.parse_line(DATA_500_QUERY, line_number=8, source_file="iis_sample.log")

    assert status == STATUS_OK
    assert ev["path"] == "/api/products?id=42"
    assert ev["status_code"] == 500
    assert ev["severity"] == "error"


def test_iis_datos_antes_de_fields_es_error():
    # Sin haber visto '#Fields:' y sin fallback, una línea de datos es 'error'.
    parser = IISParser(default_fields=[], fields_from_header=True)
    status, ev = parser.parse_line(DATA_OK, line_number=1, source_file="x.log")
    assert status == STATUS_ERROR
    assert ev is None
