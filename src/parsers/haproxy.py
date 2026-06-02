"""
haproxy.py — Parser de logs HAProxy (variante HTTP log).

QUÉ HACE
    Interpreta líneas del formato 'HTTP log' de HAProxy y las convierte en
    eventos normalizados (src/schema.py).

CUÁNDO SE INVOCA
    Lo instancia el orquestador (src/parse_logs.py) cuando la fuente detectada
    o forzada de un archivo es 'haproxy'.

ENTRADAS
    Línea cruda + nº de línea + nombre de archivo de origen.

SALIDAS
    Tupla (status, event):
        - ('ok', event)   si la línea casa el formato HTTP de HAProxy.
        - ('skip', None)  si la línea está vacía.
        - ('error', None) si la línea no casa el patrón.

QUÉ PUEDE FALLAR
    - Líneas de otro formato (TCP log, mensajes de arranque) -> 'error'.
    - accept-date ilegible -> el evento se emite con timestamp=None.

EFECTO DE PARÁMETROS
    `haproxy_log_format`: en el MVP solo se soporta 'http'. `timezone` se usa
    para etiquetar el timestamp. Cambiar el formato del log en HAProxy rompería
    el patrón y habría que actualizar la expresión regular.

REFERENCIA DEL FORMATO (campos, en orden):
    client_ip:port [accept_date] frontend backend/server Tq/Tw/Tc/Tr/Tt
    status bytes req_cookie res_cookie term_state actconn/feconn/beconn/srv/retries
    srv_queue/backend_queue [{captured_request_headers}] [{captured_response_headers}]
    "HTTP request"

    Nota (Fase 3.5): en HAProxy real es común tener "capture request header"
    (p. ej. el Host), que inserta uno o dos bloques `{...}` entre las colas y la
    petición: `... 0/0 {api-foo.example.com} "GET / HTTP/1.1"`. El patrón los
    admite como opcionales (0, 1 o 2 bloques) para parsear logs reales sin perder
    compatibilidad con líneas que no capturan cabeceras.
"""

from __future__ import annotations

import re
from typing import Optional

from src.parsers import STATUS_ERROR, STATUS_OK, STATUS_SKIP
from src.parsers.timeutils import parse_haproxy_accept_date
from src.schema import make_event

# Expresión regular del HTTP log de HAProxy. Los grupos con nombre documentan
# qué representa cada parte (ver REFERENCIA DEL FORMATO arriba).
_HAPROXY_HTTP_RE = re.compile(
    r"^\w{3}\s+\d+\s[\d:]{8}\s+"                       # prefijo syslog: 'Feb 10 14:00:01'
    r"\S+\s+"                                          # host (p. ej. lb01)
    r"haproxy\[\d+\]:\s+"                              # proceso: 'haproxy[2451]:'
    r"(?P<client_ip>[\d.]+):\d+\s+"                    # IP:puerto del cliente
    r"\[(?P<accept_date>[^\]]+)\]\s+"                  # [accept-date]
    r"(?P<frontend>\S+)\s+"                            # frontend
    r"(?P<backend>[^/]+)/(?P<server>\S+)\s+"           # backend/server
    r"(?P<tq>-?\d+)/(?P<tw>-?\d+)/(?P<tc>-?\d+)/(?P<tr>-?\d+)/(?P<tt>-?\d+)\s+"  # timers
    r"(?P<status>\d{3})\s+"                            # código de estado HTTP
    r"(?P<bytes>\d+)\s+"                               # bytes de respuesta
    r"\S+\s+\S+\s+"                                    # cookies capturadas (- -)
    r"(?P<term_state>\S+)\s+"                          # estado de terminación
    r"\d+/\d+/\d+/\d+/\d+\s+"                          # contadores de conexiones
    r"\d+/\d+\s+"                                      # colas srv/backend
    r"(?:\{[^}]*\}\s+){0,2}"                           # cabeceras capturadas opcionales {host} (Fase 3.5)
    r'"(?P<request>[^"]*)"'                            # "GET /ruta HTTP/1.1"
)


def _parse_request(request: str) -> tuple[Optional[str], Optional[str]]:
    """Extrae (método, ruta) de la petición HTTP capturada.

    Ejemplo: 'GET /api/v1/users HTTP/1.1' -> ('GET', '/api/v1/users').
    Devuelve (None, None) si la petición está vacía o es '-'.
    """
    request = request.strip()
    if not request or request == "-":
        return None, None
    parts = request.split()
    method = parts[0] if parts else None
    path = parts[1] if len(parts) > 1 else None
    return method, path


class HAProxyParser:
    """Parser de líneas HAProxy HTTP. Sin estado entre líneas."""

    source = "haproxy"

    def __init__(self, timezone: str = "UTC") -> None:
        # Zona horaria con la que se etiqueta el timestamp normalizado.
        self.timezone = timezone

    def parse_line(self, raw: str, line_number: int, source_file: str):
        """Parsea una línea. Ver contrato en src/parsers/__init__.py."""
        stripped = raw.rstrip("\n")
        if not stripped.strip():
            return STATUS_SKIP, None

        match = _HAPROXY_HTTP_RE.match(stripped)
        if match is None:
            return STATUS_ERROR, None

        g = match.groupdict()
        method, path = _parse_request(g["request"])

        # Tt (tiempo total de sesión) como duración; si es negativo (p. ej. en
        # respuestas 503 sin servidor: -1) se considera no disponible (None).
        tt = int(g["tt"])
        duration_ms = tt if tt >= 0 else None

        event = make_event(
            source=self.source,
            source_file=source_file,
            line_number=line_number,
            raw=stripped,
            timestamp=parse_haproxy_accept_date(g["accept_date"], self.timezone),
            client_ip=g["client_ip"],
            method=method,
            path=path,
            status_code=int(g["status"]),
            bytes_=int(g["bytes"]),
            duration_ms=duration_ms,
            backend=f"{g['backend']}/{g['server']}",
        )
        return STATUS_OK, event
