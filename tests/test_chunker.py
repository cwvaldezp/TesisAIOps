"""
Pruebas del Chunker (src/chunker.py) — ADR-011, Fase 2B. Cubre RF-04.

Verifican: la ventana deslizante con solape (cuántos chunks y su solape), los
metadatos de rango (líneas, timestamps, severidades), la citabilidad
(event_lines), la última ventana parcial, la validación de parámetros y el
render textual.
"""

import pytest

from src.chunker import CHUNK_FIELDS, chunk_events, render_event_line


def _evento(line_number, ts="2026-02-10T14:00:00+00:00", source="haproxy",
            severity="info", status=200):
    """Crea un evento normalizado mínimo (esquema ADR-010) para pruebas."""
    return {
        "timestamp": ts,
        "source": source,
        "severity": severity,
        "client_ip": "203.0.113.1",
        "method": "GET",
        "path": "/x",
        "status_code": status,
        "bytes": 100,
        "duration_ms": 5,
        "backend": "be_web/web01" if source == "haproxy" else None,
        "source_file": f"{source}_sample.log",
        "line_number": line_number,
        "raw": "raw",
    }


def test_numero_de_chunks_y_solape():
    """10 eventos, size=4, overlap=1 -> paso 3 -> ventanas [0:4][3:7][6:10] = 3 chunks."""
    eventos = [_evento(i) for i in range(1, 11)]  # line_number 1..10
    chunks = chunk_events(eventos, chunk_size=4, chunk_overlap=1, stem="t")

    assert len(chunks) == 3
    # Solape: el último line de un chunk reaparece como primero del siguiente.
    assert chunks[0]["line_end"] == 4 and chunks[1]["line_start"] == 4
    assert chunks[1]["line_end"] == 7 and chunks[2]["line_start"] == 7
    # IDs estables.
    assert [c["chunk_id"] for c in chunks] == ["t-0", "t-1", "t-2"]


def test_ultima_ventana_parcial_se_incluye():
    """5 eventos, size=4, overlap=0 -> [0:4] y [4:5] (parcial) = 2 chunks."""
    eventos = [_evento(i) for i in range(1, 6)]
    chunks = chunk_events(eventos, chunk_size=4, chunk_overlap=0, stem="t")
    assert len(chunks) == 2
    assert chunks[-1]["n_events"] == 1
    assert chunks[-1]["line_start"] == 5 and chunks[-1]["line_end"] == 5


def test_claves_canonicas_y_orden():
    eventos = [_evento(i) for i in range(1, 4)]
    chunk = chunk_events(eventos, chunk_size=10, chunk_overlap=0, stem="t")[0]
    assert tuple(chunk.keys()) == CHUNK_FIELDS


def test_metadatos_de_rango_y_severidades():
    eventos = [
        _evento(1, ts="2026-02-10T14:00:00+00:00", severity="info", status=200),
        _evento(2, ts="2026-02-10T14:05:00+00:00", severity="error", status=503),
        _evento(3, ts="2026-02-10T14:02:00+00:00", severity="warning", status=404),
    ]
    chunk = chunk_events(eventos, chunk_size=10, chunk_overlap=0, stem="t")[0]
    assert chunk["n_events"] == 3
    assert chunk["line_start"] == 1 and chunk["line_end"] == 3
    # ts_start/end por orden lexicográfico = cronológico (mismo offset).
    assert chunk["ts_start"] == "2026-02-10T14:00:00+00:00"
    assert chunk["ts_end"] == "2026-02-10T14:05:00+00:00"
    assert chunk["severities"] == {"info": 1, "error": 1, "warning": 1}
    assert chunk["event_lines"] == [1, 2, 3]


def test_timestamps_nulos_se_ignoran():
    eventos = [
        _evento(1, ts=None),
        _evento(2, ts="2026-02-10T14:05:00+00:00"),
    ]
    chunk = chunk_events(eventos, chunk_size=10, chunk_overlap=0, stem="t")[0]
    assert chunk["ts_start"] == "2026-02-10T14:05:00+00:00"
    assert chunk["ts_end"] == "2026-02-10T14:05:00+00:00"


def test_sources_distintas():
    eventos = [_evento(1, source="haproxy"), _evento(2, source="iis")]
    chunk = chunk_events(eventos, chunk_size=10, chunk_overlap=0, stem="t")[0]
    assert chunk["sources"] == ["haproxy", "iis"]


def test_render_event_line_contiene_campos_clave():
    linea = render_event_line(_evento(1, severity="error", status=503))
    assert "haproxy" in linea and "error" in linea and "503" in linea


def test_validacion_overlap_mayor_o_igual_size():
    eventos = [_evento(i) for i in range(1, 4)]
    with pytest.raises(ValueError):
        chunk_events(eventos, chunk_size=3, chunk_overlap=3, stem="t")


def test_lista_vacia_no_produce_chunks():
    assert chunk_events([], chunk_size=4, chunk_overlap=1, stem="t") == []
