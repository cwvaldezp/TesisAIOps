"""
timeutils.py — Utilidades de normalización de fechas/horas.

QUÉ HACE
    Convierte los distintos formatos de fecha de los logs (HAProxy e IIS) a una
    cadena ISO-8601 con sufijo de zona. Evita depender del `locale` del sistema
    (que afectaría a %b en strptime) mapeando los meses en inglés manualmente.

CUÁNDO SE INVOCA
    Desde cada parser, al construir el campo `timestamp` del evento normalizado.

ENTRADAS
    Cadenas de fecha en el formato propio de cada fuente + nombre de zona.

SALIDAS
    Cadena ISO-8601 (p. ej. '2026-02-10T14:00:01+00:00') o None si no se pudo.

QUÉ PUEDE FALLAR
    - Formato inesperado -> devuelve None (el parser decide cómo tratarlo).

EFECTO DE PARÁMETROS
    `timezone` (de config) se anexa como etiqueta de zona. En el MVP se asume
    que los timestamps de los logs ya están en esa zona (no se reconvierten).
"""

from __future__ import annotations

from typing import Optional

# Mapa de abreviaturas de mes en inglés -> número. Evita la dependencia del
# locale al parsear el accept-date de HAProxy (p. ej. "10/Feb/2026:...").
_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# Sufijos de zona conocidos para no depender de librerías externas en el MVP.
# Si la zona no está aquí, se anexa como nombre informativo sin offset numérico.
_TZ_SUFFIX = {
    "UTC": "+00:00",
    "GMT": "+00:00",
}


def _tz_suffix(timezone: str) -> str:
    """Devuelve el sufijo de offset para una zona conocida (UTC por defecto)."""
    return _TZ_SUFFIX.get(timezone.upper(), "+00:00")


def parse_haproxy_accept_date(value: str, timezone: str = "UTC") -> Optional[str]:
    """Convierte el accept-date de HAProxy a ISO-8601.

    Formato de entrada: 'dd/Mon/YYYY:HH:MM:SS.mmm'  (ej. '10/Feb/2026:14:00:01.123')
    """
    try:
        date_part, time_part = value.split(":", 1)  # '10/Feb/2026', 'HH:MM:SS.mmm'
        day_s, mon_s, year_s = date_part.split("/")
        month = _MONTHS.get(mon_s)
        if month is None:
            return None
        # time_part = 'HH:MM:SS.mmm' -> nos quedamos con HH:MM:SS (ignoramos ms).
        hms = time_part.split(".")[0]
        iso = f"{int(year_s):04d}-{month:02d}-{int(day_s):02d}T{hms}{_tz_suffix(timezone)}"
        return iso
    except (ValueError, KeyError):
        return None


def parse_iis_datetime(date_s: str, time_s: str, timezone: str = "UTC") -> Optional[str]:
    """Combina los campos `date` y `time` de IIS (W3C) en ISO-8601.

    Formato de entrada: date='YYYY-MM-DD', time='HH:MM:SS'.
    """
    try:
        if not date_s or not time_s or date_s == "-" or time_s == "-":
            return None
        # Validación ligera del formato esperado.
        y, m, d = date_s.split("-")
        hh, mm, ss = time_s.split(":")
        iso = (
            f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
            f"T{int(hh):02d}:{int(mm):02d}:{int(ss):02d}{_tz_suffix(timezone)}"
        )
        return iso
    except ValueError:
        return None
