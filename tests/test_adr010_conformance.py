"""
Pruebas de CONFORMIDAD de los parsers con el contrato ADR-010.

  - HAProxy: Fase 1.2.
  - IIS (W3C): Fase 1.3.

Estas pruebas no validan "que parsee" (eso lo cubren test_haproxy_parser.py y
test_iis_parser.py), sino que el evento resultante **cumple el contrato del
esquema normalizado** formalizado en ADR-010, para CADA fuente:
  - las 13 claves canónicas están SIEMPRE presentes y en orden;
  - los 5 campos núcleo nunca son nulos;
  - la severidad se deriva del status (regla 5xx/4xx/resto);
  - los campos opcionales que la fuente no provee quedan en null (no se omiten);
  - el evento es serializable a JSON sin pérdida.

Cubre: RF-03, RNF-05 (citabilidad). Ancla de defensa: P-13, P-14, P-16, P-17.
"""

import json

from src.parsers import STATUS_OK
from src.parsers.haproxy import HAProxyParser
from src.parsers.iis import IISParser
from src.schema import EVENT_FIELDS

# Campos que el contrato ADR-010 garantiza NO nulos (núcleo).
CORE_NON_NULL = ("source", "severity", "source_file", "line_number", "raw")

LINE_200 = (
    "Feb 10 14:00:01 lb01 haproxy[2451]: 203.0.113.10:51234 "
    "[10/Feb/2026:14:00:01.123] fe_http be_web/web01 0/0/1/12/13 200 2456 "
    '- - ---- 12/12/3/1/0 0/0 "GET /index.html HTTP/1.1"'
)
LINE_503 = (
    "Feb 10 14:03:11 lb01 haproxy[2451]: 203.0.113.15:51288 "
    "[10/Feb/2026:14:03:11.005] fe_http be_api/<NOSRV> 0/-1/-1/-1/0 503 213 "
    '- - SC-- 20/20/9/0/0 0/0 "GET /api/v1/orders HTTP/1.1"'
)
# Línea con petición vacía (cliente que no envía una request válida): permite
# demostrar que un campo opcional sin dato queda en null, sin omitir la clave.
LINE_SIN_REQUEST = (
    "Feb 10 14:04:00 lb01 haproxy[2451]: 203.0.113.30:51400 "
    "[10/Feb/2026:14:04:00.000] fe_http be_web/web01 0/0/0/0/0 400 0 "
    '- - ---- 12/12/3/1/0 0/0 ""'
)


def _parse(line: str) -> dict:
    status, event = HAProxyParser(timezone="UTC").parse_line(
        line, line_number=1, source_file="demo.log"
    )
    assert status == STATUS_OK
    return event


def test_contrato_13_claves_presentes_y_en_orden():
    """ADR-010: el evento expone exactamente las 13 claves canónicas, en orden."""
    event = _parse(LINE_200)
    assert tuple(event.keys()) == EVENT_FIELDS
    assert len(EVENT_FIELDS) == 13


def test_campos_nucleo_no_nulos():
    """ADR-010: los 5 campos núcleo nunca son nulos (garantizan citabilidad)."""
    for line in (LINE_200, LINE_503):
        event = _parse(line)
        for campo in CORE_NON_NULL:
            assert event[campo] is not None, f"{campo} no debe ser nulo"
        # source siempre identifica la fuente.
        assert event["source"] == "haproxy"


def test_severidad_derivada_del_status():
    """ADR-010: severity se deriva del status (5xx=error, 4xx=warning, resto=info)."""
    assert _parse(LINE_200)["severity"] == "info"   # 200
    assert _parse(LINE_503)["severity"] == "error"  # 503


def test_citabilidad_presente():
    """ADR-010/RNF-05: el evento conserva la evidencia para poder citar."""
    event = _parse(LINE_200)
    assert event["source_file"] == "demo.log"
    assert event["line_number"] == 1
    assert event["raw"] == LINE_200  # línea original íntegra


def test_opcionales_nulos_no_se_omiten():
    """ADR-010: un opcional no disponible queda en null, la clave sigue presente.

    Con una petición vacía, `method` y `path` no se pueden extraer -> deben ser
    null, pero sus claves deben seguir existiendo (esquema fijo, no se omiten).
    """
    event = _parse(LINE_SIN_REQUEST)
    assert "method" in event and "path" in event
    assert event["method"] is None
    assert event["path"] is None
    # El esquema sigue completo aunque haya nulos.
    assert tuple(event.keys()) == EVENT_FIELDS


def test_evento_serializable_a_json():
    """ADR-010: el evento se serializa a JSON sin pérdida (flujo log->JSON)."""
    event = _parse(LINE_503)
    texto = json.dumps(event, ensure_ascii=False)
    reconstruido = json.loads(texto)
    assert reconstruido == event
    assert reconstruido["backend"] == "be_api/<NOSRV>"


# =============================================================================
# Conformidad del parser IIS (W3C) con ADR-010 — Fase 1.3
# =============================================================================

# Cabecera W3C que declara las columnas (el parser IIS es estatal: la necesita
# antes de las líneas de datos).
IIS_FIELDS = (
    "#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port "
    "cs-username c-ip cs(User-Agent) sc-status sc-substatus sc-win32-status time-taken"
)
IIS_200 = (
    "2026-02-10 14:00:01 198.51.100.5 GET /home - 443 - 203.0.113.10 "
    "Mozilla/5.0+(Windows+NT+10.0) 200 0 0 35"
)
IIS_500_QUERY = (
    "2026-02-10 14:00:09 198.51.100.6 GET /api/products id=42 443 - 203.0.113.13 "
    "Mozilla/5.0+(iPhone) 500 0 2 1985"
)
IIS_404 = (
    "2026-02-10 14:00:12 198.51.100.6 GET /favicon.ico - 443 - 203.0.113.14 "
    "Mozilla/5.0+(X11) 404 0 2 8"
)


def _parse_iis(data_line: str) -> dict:
    """Crea un parser IIS, le da la cabecera #Fields y parsea una línea de datos."""
    parser = IISParser(timezone="UTC")
    parser.parse_line(IIS_FIELDS, line_number=1, source_file="iis.log")  # define columnas
    status, event = parser.parse_line(data_line, line_number=2, source_file="iis.log")
    assert status == STATUS_OK
    return event


def test_iis_contrato_13_claves_presentes_y_en_orden():
    """ADR-010: el evento IIS expone exactamente las 13 claves canónicas, en orden."""
    event = _parse_iis(IIS_200)
    assert tuple(event.keys()) == EVENT_FIELDS


def test_iis_campos_nucleo_no_nulos():
    """ADR-010: los 5 campos núcleo nunca son nulos también para IIS."""
    for line in (IIS_200, IIS_500_QUERY, IIS_404):
        event = _parse_iis(line)
        for campo in CORE_NON_NULL:
            assert event[campo] is not None, f"{campo} no debe ser nulo"
        assert event["source"] == "iis"


def test_iis_severidad_derivada_del_status():
    """ADR-010: severity se deriva del sc-status (mismo criterio que HAProxy)."""
    assert _parse_iis(IIS_200)["severity"] == "info"       # 200
    assert _parse_iis(IIS_404)["severity"] == "warning"    # 404
    assert _parse_iis(IIS_500_QUERY)["severity"] == "error"  # 500


def test_iis_backend_y_bytes_nulos_pero_presentes():
    """ADR-010: IIS no expone backend ni bytes (campos por defecto) -> null, sin omitir.

    Demuestra el principio 'esquema fijo, valores nullable': la fuente IIS no
    tiene concepto de backend y el set W3C por defecto no incluye sc-bytes, así
    que ambas claves valen null pero SIGUEN presentes.
    """
    event = _parse_iis(IIS_200)
    assert "backend" in event and event["backend"] is None
    assert "bytes" in event and event["bytes"] is None


def test_iis_path_combina_stem_y_query():
    """ADR-010: el mapeo IIS combina cs-uri-stem + cs-uri-query en `path`."""
    assert _parse_iis(IIS_200)["path"] == "/home"            # sin query
    assert _parse_iis(IIS_500_QUERY)["path"] == "/api/products?id=42"


def test_iis_citabilidad_presente():
    """ADR-010/RNF-05: el evento IIS conserva la evidencia para poder citar."""
    event = _parse_iis(IIS_200)
    assert event["source_file"] == "iis.log"
    assert event["line_number"] == 2
    assert event["raw"] == IIS_200


def test_iis_evento_serializable_a_json():
    """ADR-010: el evento IIS se serializa a JSON sin pérdida (flujo log->JSON)."""
    event = _parse_iis(IIS_500_QUERY)
    reconstruido = json.loads(json.dumps(event, ensure_ascii=False))
    assert reconstruido == event
    assert reconstruido["source"] == "iis"
    assert reconstruido["duration_ms"] == 1985  # time-taken en ms
