"""
ingest.py — Lectura de archivos de log (texto plano y .gz) y descubrimiento.

QUÉ HACE
    Aísla "cómo se obtienen las líneas crudas" del resto del pipeline:
    1) `read_log_lines`: lee un archivo de log devolviendo sus líneas,
       descomprimiendo **al vuelo** si la extensión es `.gz` (gzip, stdlib).
    2) `discover_log_files`: enumera los archivos de log bajo una carpeta según
       uno o más patrones glob, con opción recursiva (subcarpetas por aplicación).

CUÁNDO SE INVOCA
    Lo usa el orquestador de parsing (`src/parse_logs.py`) y el arnés de
    validación con corpus real (`src/validate_corpus.py`, Fase 3.5).

ENTRADAS
    - Ruta a un archivo (`.log` o `.gz`) + encoding (read_log_lines).
    - Carpeta raíz + lista de patrones glob + flag recursivo (discover_log_files).

SALIDAS
    - read_log_lines -> list[str] (líneas sin el salto final).
    - discover_log_files -> list[Path] ordenada y sin duplicados.

QUÉ PUEDE FALLAR
    - Archivo inexistente / corrupto -> excepción de E/S (la maneja el llamador).
    - Bytes no decodificables -> se reemplazan (errors='replace') para no abortar
      una corrida de corpus real por una línea con basura.

EFECTO DE PARÁMETROS
    `recursive` decide si se exploran subcarpetas; `patterns` decide qué
    extensiones entran (p. ej. ['*.log'] o ['*.log', '*.gz']). NUNCA escribe ni
    toca infraestructura (ADR-005): es solo lectura.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Iterable

# Extensión que dispara la descompresión transparente.
_GZIP_SUFFIX = ".gz"


def read_log_lines(path: str | Path, encoding: str = "utf-8") -> list[str]:
    """Lee un archivo de log y devuelve sus líneas (sin el salto final).

    Si el archivo termina en `.gz` se descomprime al vuelo con gzip; en caso
    contrario se lee como texto plano. Los bytes no decodificables se reemplazan
    (no se aborta la corrida por una línea con basura en un corpus real).
    """
    path = Path(path)
    opener = gzip.open if path.suffix.lower() == _GZIP_SUFFIX else open
    with opener(path, "rt", encoding=encoding, errors="replace") as fh:
        text = fh.read()
    return text.splitlines()


def discover_log_files(
    root: str | Path,
    patterns: Iterable[str] = ("*.log",),
    *,
    recursive: bool = False,
) -> list[Path]:
    """Enumera los archivos de log bajo `root` que casan alguno de `patterns`.

    - `recursive=False`: solo el primer nivel de `root` (glob).
    - `recursive=True`: explora subcarpetas (rglob) — útil para el corpus real,
      organizado en una subcarpeta por aplicación.
    Devuelve una lista **ordenada y sin duplicados** (un archivo puede casar más
    de un patrón). Las carpetas se descartan.
    """
    root = Path(root)
    glob_fn = root.rglob if recursive else root.glob

    seen: set[Path] = set()
    for pattern in patterns:
        for p in glob_fn(pattern):
            if p.is_file():
                seen.add(p)
    return sorted(seen)
