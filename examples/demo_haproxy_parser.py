"""
demo_haproxy_parser.py — Demostración del flujo de parseo HAProxy (Fase 1.2).

PROPÓSITO
    Mostrar, de forma mínima y didáctica, el objetivo demostrable de la Fase 1.2:

        línea de log HAProxy  ->  parse_line()  ->  evento normalizado  ->  JSON

    NO reimplementa el parser: lo *usa* (`src/parsers/haproxy.py`) para evidenciar
    que cumple el contrato del esquema normalizado (ADR-010).

ENTRADAS
    Ninguna por argumentos. Usa dos líneas HAProxy de ejemplo embebidas (una
    petición 200 OK y un incidente 503 sin servidor `<NOSRV>`).

SALIDAS
    Imprime por consola, para cada línea: la línea cruda, el evento normalizado
    como diccionario y su serialización JSON (indentada). Código de salida 0.

DEPENDENCIAS
    src.parsers.haproxy.HAProxyParser, src.parsers (STATUS_OK), json.
    No usa embeddings, FAISS, RAG ni LLM (fuera del alcance de la fase).

RIESGOS
    Es solo demostrativo (solo lectura, sin tocar infraestructura — ADR-005).
    Si el contrato del parser cambiara, este demo lo reflejaría de inmediato.

IMPACTO DE CAMBIOS
    Si se modifica el esquema (ADR-010) o el formato de log, la salida de este
    demo cambia; sirve como verificación visual rápida del flujo.

EJECUCIÓN
    python -m examples.demo_haproxy_parser
"""

from __future__ import annotations

import json

from src.parsers import STATUS_OK
from src.parsers.haproxy import HAProxyParser

# Dos líneas HAProxy de ejemplo (anonimizadas, IPs de documentación RFC 5737):
#   1) Petición normal 200 OK.
#   2) Incidente: backend sin servidor disponible (<NOSRV>) -> 503.
LINEAS_DEMO = [
    (
        "Feb 10 14:00:01 lb01 haproxy[2451]: 203.0.113.10:51234 "
        "[10/Feb/2026:14:00:01.123] fe_http be_web/web01 0/0/1/12/13 200 2456 "
        '- - ---- 12/12/3/1/0 0/0 "GET /index.html HTTP/1.1"'
    ),
    (
        "Feb 10 14:03:11 lb01 haproxy[2451]: 203.0.113.15:51288 "
        "[10/Feb/2026:14:03:11.005] fe_http be_api/<NOSRV> 0/-1/-1/-1/0 503 213 "
        '- - SC-- 20/20/9/0/0 0/0 "GET /api/v1/orders HTTP/1.1"'
    ),
]


def main() -> int:
    """Recorre las líneas de ejemplo y muestra el flujo log -> evento -> JSON."""
    parser = HAProxyParser(timezone="UTC")

    for i, linea in enumerate(LINEAS_DEMO, start=1):
        # Paso 1: la línea cruda de entrada.
        print(f"\n=== Línea {i} (entrada cruda) ===")
        print(linea)

        # Paso 2: parse_line() devuelve (estado, evento).
        status, evento = parser.parse_line(linea, line_number=i, source_file="demo.log")

        if status != STATUS_OK:
            print(f"  [estado={status}] no se pudo parsear la línea.")
            continue

        # Paso 3: el evento normalizado (esquema común de 13 campos, ADR-010).
        print("--- Evento normalizado (dict) ---")
        print(evento)

        # Paso 4: serialización a JSON (lo que consumirán las fases siguientes).
        print("--- JSON (ADR-010) ---")
        print(json.dumps(evento, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
