"""
iis.py — Parser de logs IIS en formato W3C Extended.

QUÉ HACE
    Interpreta logs W3C de IIS. Las columnas se definen en una directiva
    '#Fields:' dentro del propio archivo; este parser la lee y mapea cada
    columna por posición al esquema normalizado (src/schema.py).

CUÁNDO SE INVOCA
    Lo instancia el orquestador (src/parse_logs.py) cuando la fuente detectada
    o forzada de un archivo es 'iis'. El parser es ESTATAL por archivo: recuerda
    las columnas declaradas en '#Fields:' para las líneas de datos siguientes.

ENTRADAS
    Línea cruda + nº de línea + nombre de archivo de origen.

SALIDAS
    Tupla (status, event):
        - ('ok', event)   línea de datos parseada.
        - ('skip', None)  línea vacía o directiva '#...' (incluida '#Fields').
        - ('error', None) línea de datos sin columnas conocidas o mal formada.

QUÉ PUEDE FALLAR
    - Archivo sin '#Fields:' y sin `iis_fields` de fallback -> todas las líneas
      de datos serán 'error'.
    - Nº de columnas distinto al de '#Fields:' -> 'error' para esa línea.

EFECTO DE PARÁMETROS
    - `iis_fields_from_header`: si True, las columnas se toman del archivo; si
      False, se usan siempre las de `iis_fields` (config).
    - `iis_fields`: columnas de fallback cuando no hay cabecera.
    - `timezone`: etiqueta del timestamp.
"""

from __future__ import annotations

from typing import Optional

from src.parsers import STATUS_ERROR, STATUS_OK, STATUS_SKIP
from src.parsers.timeutils import parse_iis_datetime
from src.schema import make_event

# Valor que IIS usa para campos ausentes.
_EMPTY = "-"


def _to_int(value: Optional[str]) -> Optional[int]:
    """Convierte a int de forma tolerante; devuelve None si no aplica."""
    if value is None or value == _EMPTY:
        return None
    try:
        return int(value)
    except ValueError:
        return None


class IISParser:
    """Parser de líneas IIS W3C. Mantiene las columnas declaradas en '#Fields:'."""

    source = "iis"

    def __init__(
        self,
        timezone: str = "UTC",
        default_fields: Optional[list[str]] = None,
        fields_from_header: bool = True,
    ) -> None:
        self.timezone = timezone
        self.fields_from_header = fields_from_header
        # Columnas activas. Si no se toman del header, se usan las de config.
        self.fields: Optional[list[str]] = (
            None if fields_from_header else list(default_fields or [])
        )
        # Fallback si el archivo no trae '#Fields:'.
        self._default_fields = list(default_fields or [])

    def parse_line(self, raw: str, line_number: int, source_file: str):
        """Parsea una línea. Ver contrato en src/parsers/__init__.py."""
        stripped = raw.rstrip("\n")
        if not stripped.strip():
            return STATUS_SKIP, None

        # Directivas W3C (empiezan por '#'). La de '#Fields:' define las columnas.
        if stripped.startswith("#"):
            if self.fields_from_header and stripped.lower().startswith("#fields:"):
                # '#Fields: date time s-ip ...' -> lista de nombres de columna.
                self.fields = stripped.split(":", 1)[1].split()
            return STATUS_SKIP, None

        # Si aún no hay columnas, intentamos el fallback de config.
        fields = self.fields if self.fields else self._default_fields
        if not fields:
            return STATUS_ERROR, None

        values = stripped.split()
        if len(values) != len(fields):
            # Recuento de columnas inconsistente con la cabecera -> no fiable.
            return STATUS_ERROR, None

        row = dict(zip(fields, values))

        status_code = _to_int(row.get("sc-status"))
        # IIS reporta time-taken en milisegundos.
        duration_ms = _to_int(row.get("time-taken"))

        # Ruta: combinamos stem + query si esta última existe.
        path = row.get("cs-uri-stem")
        query = row.get("cs-uri-query")
        if path and query and query != _EMPTY:
            path = f"{path}?{query}"

        event = make_event(
            source=self.source,
            source_file=source_file,
            line_number=line_number,
            raw=stripped,
            timestamp=parse_iis_datetime(
                row.get("date", ""), row.get("time", ""), self.timezone
            ),
            client_ip=None if row.get("c-ip") in (None, _EMPTY) else row.get("c-ip"),
            method=None if row.get("cs-method") in (None, _EMPTY) else row.get("cs-method"),
            path=path,
            status_code=status_code,
            bytes_=_to_int(row.get("sc-bytes")),  # ausente en el set por defecto -> None
            duration_ms=duration_ms,
            backend=None,  # IIS no expone backend en este formato
        )
        return STATUS_OK, event
