"""
schema.py — Esquema normalizado común de eventos de log.

QUÉ HACE
    Define el modelo de datos único al que se reducen TODAS las fuentes de log
    (HAProxy e IIS), según la decisión ADR-003. También deriva la severidad a
    partir del código de estado HTTP y ofrece un constructor canónico de eventos.

CUÁNDO SE INVOCA
    Lo usan los parsers (src/parsers/*) al transformar una línea cruda en un
    evento normalizado, y el orquestador (src/parse_logs.py) al serializar.

ENTRADAS
    Campos sueltos ya extraídos por un parser (timestamp, status_code, etc.).

SALIDAS
    Un diccionario con las claves del esquema, en orden estable (apto para JSON).

QUÉ PUEDE FALLAR
    - status_code no numérico → se trata como None y la severidad será 'info'.
    Ningún fallo detiene el proceso: este módulo es puramente de construcción.

EFECTO DE PARÁMETROS
    Los umbrales de severidad son constantes de diseño (no configurables en el
    MVP). Si cambiaran, afectarían cómo se clasifica cada evento.
"""

from __future__ import annotations

from typing import Any, Optional

# Orden canónico de los campos del evento normalizado.
# Se mantiene estable para que la salida JSON sea predecible y diff-eable.
EVENT_FIELDS = (
    "timestamp",     # str ISO-8601 | None  — fecha/hora normalizada del evento
    "source",        # str                  — 'haproxy' | 'iis'
    "severity",      # str                  — 'info' | 'warning' | 'error'
    "client_ip",     # str | None           — IP del cliente
    "method",        # str | None           — método HTTP
    "path",          # str | None           — ruta solicitada (con query si aplica)
    "status_code",   # int | None           — código de estado HTTP
    "bytes",         # int | None           — bytes de respuesta
    "duration_ms",   # int | None           — latencia / tiempo de servicio (ms)
    "backend",       # str | None           — backend/servidor (solo HAProxy)
    "source_file",   # str                  — archivo de origen (para citar)
    "line_number",   # int                  — nº de línea de origen (para citar)
    "raw",           # str                  — línea original íntegra (evidencia)
)


def derive_severity(status_code: Optional[int]) -> str:
    """Deriva la severidad del evento a partir del código de estado HTTP.

    Regla de diseño (no configurable en el MVP):
        - 5xx  -> 'error'    (fallo del servidor/backend)
        - 4xx  -> 'warning'  (error del cliente / recurso no encontrado)
        - resto / desconocido -> 'info'
    """
    if status_code is None:
        return "info"
    if 500 <= status_code <= 599:
        return "error"
    if 400 <= status_code <= 499:
        return "warning"
    return "info"


def make_event(
    *,
    source: str,
    source_file: str,
    line_number: int,
    raw: str,
    timestamp: Optional[str] = None,
    client_ip: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    bytes_: Optional[int] = None,
    duration_ms: Optional[int] = None,
    backend: Optional[str] = None,
) -> dict[str, Any]:
    """Construye un evento normalizado con las claves en el orden canónico.

    La severidad se deriva automáticamente del `status_code` (no se pasa a mano)
    para garantizar coherencia entre fuentes.
    """
    event = {
        "timestamp": timestamp,
        "source": source,
        "severity": derive_severity(status_code),
        "client_ip": client_ip,
        "method": method,
        "path": path,
        "status_code": status_code,
        "bytes": bytes_,
        "duration_ms": duration_ms,
        "backend": backend,
        "source_file": source_file,
        "line_number": line_number,
        "raw": raw,
    }
    # Reordena según EVENT_FIELDS para garantizar salida estable.
    return {k: event[k] for k in EVENT_FIELDS}


def make_unparsed_event(
    *, source: str, source_file: str, line_number: int, raw: str
) -> dict[str, Any]:
    """Evento mínimo para líneas no parseables cuando `on_parse_error='keep'`.

    Conserva la trazabilidad (archivo, línea, contenido) aunque no se hayan
    podido extraer campos. La severidad por defecto es 'info'.
    """
    return make_event(
        source=source,
        source_file=source_file,
        line_number=line_number,
        raw=raw,
    )
