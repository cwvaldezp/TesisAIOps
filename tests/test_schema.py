"""
Pruebas del esquema normalizado (src/schema.py).

Verifican la derivación de severidad y el orden canónico de los campos del
evento, que es la base de la salida JSON (RF-03).
"""

from src.schema import EVENT_FIELDS, derive_severity, make_event


def test_derive_severity_por_rango():
    assert derive_severity(200) == "info"
    assert derive_severity(301) == "info"
    assert derive_severity(404) == "warning"
    assert derive_severity(499) == "warning"
    assert derive_severity(500) == "error"
    assert derive_severity(503) == "error"
    assert derive_severity(None) == "info"  # sin código -> info


def test_make_event_orden_y_severidad():
    ev = make_event(
        source="haproxy",
        source_file="x.log",
        line_number=7,
        raw="linea cruda",
        status_code=503,
    )
    # El orden de claves debe coincidir exactamente con EVENT_FIELDS.
    assert tuple(ev.keys()) == EVENT_FIELDS
    # La severidad se deriva automáticamente del status_code.
    assert ev["severity"] == "error"
    assert ev["source_file"] == "x.log"
    assert ev["line_number"] == 7
