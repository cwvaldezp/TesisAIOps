"""
chunker.py — Agrupa eventos normalizados en chunks (ADR-011, Fase 2B).

PROPÓSITO
    Convertir una secuencia de eventos normalizados (esquema ADR-010) en
    **chunks**: ventanas de N eventos consecutivos con solape, cada una con su
    texto (para futuro embedding) y metadatos de rango (para citabilidad).
    Es la unidad que la Fase 2C vectorizará. NO usa embeddings ni librerías de IA.

ENTRADAS
    - events: lista de eventos normalizados (dicts con las 13 claves de ADR-010).
    - chunk_size: nº de eventos por chunk (> 0).
    - chunk_overlap: solape en eventos (0 <= overlap < chunk_size).
    - stem: prefijo para el chunk_id (p. ej. 'haproxy_sample').

SALIDAS
    Lista de chunks (dicts) con el esquema descrito en docs/03_flujos.md §2.2:
    chunk_id, source_file, sources, line_start/end, ts_start/end, n_events,
    severities, event_lines, text.

DEPENDENCIAS
    Solo librería estándar (no embeddings, no vector store, no IA).

RIESGOS
    - chunk_overlap >= chunk_size -> ValueError (evita avance nulo / bucle).
    - Eventos sin timestamp -> ts_start/ts_end se calculan ignorando los nulos.

IMPACTO DE CAMBIOS
    Cambiar el tamaño/solape o el render del texto cambia los chunks producidos y
    obliga a re-chunkear (y a reindexar en fases posteriores).
"""

from __future__ import annotations

from typing import Any, Optional

# Orden canónico de las claves del chunk (salida estable, diff-eable).
CHUNK_FIELDS = (
    "chunk_id",
    "source_file",
    "sources",
    "line_start",
    "line_end",
    "ts_start",
    "ts_end",
    "n_events",
    "severities",
    "event_lines",
    "text",
)


def render_event_line(event: dict[str, Any]) -> str:
    """Renderiza un evento como una línea compacta y legible para el `text`.

    Ejemplo:
        [2026-02-10T14:03:11+00:00] haproxy error GET /api/v1/orders 503 0ms be_api/<NOSRV>

    Los campos ausentes (None) se muestran como '-'. Este texto es lo que en la
    Fase 2C se convertirá en embedding, así que prioriza señal sobre formato.
    """
    def g(key: str) -> str:
        value = event.get(key)
        return "-" if value is None else str(value)

    ts = g("timestamp")
    source = g("source")
    severity = g("severity")
    method = g("method")
    path = g("path")
    status = g("status_code")
    duration = event.get("duration_ms")
    dur = "-" if duration is None else f"{duration}ms"
    backend = g("backend")
    return f"[{ts}] {source} {severity} {method} {path} {status} {dur} {backend}"


def _min_max_timestamps(events: list[dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
    """Devuelve (ts_start, ts_end) ignorando timestamps nulos.

    Los timestamps son ISO-8601 con la misma zona, por lo que el orden
    lexicográfico coincide con el cronológico (no hace falta parsear fechas).
    """
    ts = [e["timestamp"] for e in events if e.get("timestamp")]
    if not ts:
        return None, None
    return min(ts), max(ts)


def _build_chunk(window: list[dict[str, Any]], index: int, stem: str) -> dict[str, Any]:
    """Construye un chunk (con metadatos de rango) a partir de una ventana."""
    line_numbers = [e.get("line_number") for e in window if e.get("line_number") is not None]
    ts_start, ts_end = _min_max_timestamps(window)

    # Conteo de severidades presentes en el chunk.
    severities: dict[str, int] = {}
    for e in window:
        sev = e.get("severity", "info")
        severities[sev] = severities.get(sev, 0) + 1

    # Fuentes y archivo(s) de origen presentes (normalmente uno solo).
    sources = sorted({e.get("source") for e in window if e.get("source")})
    source_files = sorted({e.get("source_file") for e in window if e.get("source_file")})
    source_file = source_files[0] if len(source_files) == 1 else ",".join(source_files)

    text = "\n".join(render_event_line(e) for e in window)

    chunk = {
        "chunk_id": f"{stem}-{index}",
        "source_file": source_file,
        "sources": sources,
        "line_start": line_numbers[0] if line_numbers else None,
        "line_end": line_numbers[-1] if line_numbers else None,
        "ts_start": ts_start,
        "ts_end": ts_end,
        "n_events": len(window),
        "severities": severities,
        "event_lines": line_numbers,
        "text": text,
    }
    # Reordena según CHUNK_FIELDS para salida estable.
    return {k: chunk[k] for k in CHUNK_FIELDS}


def chunk_events(
    events: list[dict[str, Any]],
    *,
    chunk_size: int,
    chunk_overlap: int,
    stem: str,
) -> list[dict[str, Any]]:
    """Agrupa eventos en ventanas de `chunk_size` con `chunk_overlap` (ADR-011).

    Estrategia 'by_events': ventana deslizante de tamaño fijo. El paso es
    (chunk_size - chunk_overlap). La última ventana puede ser parcial (incluye el
    resto de eventos) y cierra el recorrido.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size debe ser > 0 (es {chunk_size}).")
    if not (0 <= chunk_overlap < chunk_size):
        raise ValueError(
            f"chunk_overlap debe cumplir 0 <= overlap < chunk_size "
            f"(overlap={chunk_overlap}, chunk_size={chunk_size})."
        )

    step = chunk_size - chunk_overlap
    chunks: list[dict[str, Any]] = []
    n = len(events)
    i = 0
    index = 0
    while i < n:
        window = events[i : i + chunk_size]
        chunks.append(_build_chunk(window, index, stem))
        index += 1
        # Si esta ventana ya llegó al final, no generamos una cola duplicada.
        if i + chunk_size >= n:
            break
        i += step
    return chunks
