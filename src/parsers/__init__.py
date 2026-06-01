"""
Paquete `src.parsers` — parsers específicos por fuente de log.

Cada parser convierte líneas crudas de su formato a eventos normalizados
(esquema común, ver src/schema.py). Todos exponen el mismo contrato:

    parser.parse_line(raw, line_number, source_file) -> (status, event)

donde `status` es uno de:
    - 'ok'    : la línea se parseó; `event` es el dict normalizado.
    - 'skip'  : línea legítimamente ignorable (vacía, comentario, directiva);
                no es un error y no se contabiliza como tal. `event` es None.
    - 'error' : la línea no se pudo parsear; `event` es None. El orquestador
                decide qué hacer según `on_parse_error`.

Este contrato uniforme permite al orquestador (src/parse_logs.py) tratar todas
las fuentes igual.
"""

# Estados posibles del resultado de parsear una línea.
STATUS_OK = "ok"
STATUS_SKIP = "skip"
STATUS_ERROR = "error"
