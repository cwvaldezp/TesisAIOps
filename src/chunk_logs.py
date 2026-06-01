"""
chunk_logs.py — Orquestador CLI del Chunker (ADR-011, Fase 2B).

PROPÓSITO
    Pega el subflujo de chunking (docs/03_flujos.md §2.2):
    1) localiza los archivos `*.events.jsonl` en processed_path,
    2) carga los eventos de cada uno,
    3) los agrupa en chunks (src/chunker.py) según la config,
    4) escribe `<stem>.chunks.jsonl` por cada archivo de eventos,
    5) imprime un resumen.

CUÁNDO / QUIÉN LO INVOCA
    Manualmente, como paso offline de solo lectura tras el parser:
        python -m src.chunk_logs
        python -m src.chunk_logs --chunk-size 10 --chunk-overlap 2

ENTRADAS
    config/config.yaml (sección `chunking`) + archivos `*.events.jsonl`.

SALIDAS
    Un archivo `<stem>.chunks.jsonl` por archivo de eventos, en processed_path,
    + un resumen por consola. Código de salida 0 si todo fue bien.

DEPENDENCIAS
    src.config, src.chunker. Solo stdlib (sin embeddings ni librerías de IA).

RIESGOS
    - processed_path sin `*.events.jsonl` -> error claro y aborta.
    - Línea JSONL corrupta -> se reporta el archivo/línea y aborta ese archivo.

IMPACTO DE CAMBIOS
    Los parámetros provienen de la config (ADR-011, ver docs/04). Cambiar
    chunk_size/overlap obliga a re-chunkear. NUNCA toca infraestructura (ADR-005).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.chunker import chunk_events
from src.config import Config, load_config

# Sufijos de archivo de eventos (entrada) y de chunks (salida).
EVENTS_SUFFIX = ".events.jsonl"
CHUNKS_SUFFIX = ".chunks.jsonl"


def load_events(path: Path) -> list[dict[str, Any]]:
    """Carga un archivo JSONL de eventos (un objeto por línea)."""
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido en {path.name}:{i} -> {exc}") from exc
    return events


def write_chunks(chunks: list[dict[str, Any]], out_path: Path) -> None:
    """Escribe los chunks como JSONL (un chunk por línea)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for ch in chunks:
            fh.write(json.dumps(ch, ensure_ascii=False) + "\n")


def run(cfg: Config) -> int:
    """Ejecuta el chunking sobre todos los `*.events.jsonl`. Devuelve exit code."""
    processed_dir = Path(cfg.processed_path)
    if not processed_dir.exists():
        print(f"[ERROR] No existe processed_path: {processed_dir}", file=sys.stderr)
        return 1

    files = sorted(processed_dir.glob(f"*{EVENTS_SUFFIX}"))
    if not files:
        print(
            f"[ERROR] No hay archivos '*{EVENTS_SUFFIX}' en {processed_dir}. "
            "Ejecute antes el parser (python -m src.parse_logs).",
            file=sys.stderr,
        )
        return 1

    print("== TesisAIOps · Chunker (Fase 2B, ADR-011) ==")
    print(f"Carpeta        : {processed_dir}")
    print(f"Estrategia     : {cfg.chunk_strategy}  size={cfg.chunk_size}  overlap={cfg.chunk_overlap}")
    print("-" * 60)

    total_chunks = 0
    for path in files:
        # stem sin el sufijo '.events.jsonl' (p. ej. 'haproxy_sample').
        stem = path.name[: -len(EVENTS_SUFFIX)]
        events = load_events(path)
        chunks = chunk_events(
            events,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            stem=stem,
        )
        out_path = processed_dir / f"{stem}{CHUNKS_SUFFIX}"
        write_chunks(chunks, out_path)
        total_chunks += len(chunks)
        print(
            f"{path.name:30} eventos={len(events):3}  chunks={len(chunks):3}  -> {out_path.name}"
        )

    print("-" * 60)
    print(f"TOTAL: {len(files)} archivo(s), {total_chunks} chunk(s) escritos.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI. Permite overrides puntuales de chunk_size/overlap."""
    ap = argparse.ArgumentParser(
        description="Chunker: *.events.jsonl -> *.chunks.jsonl (ADR-011, sin IA)."
    )
    ap.add_argument("--config", default="config/config.yaml", help="Ruta al YAML.")
    ap.add_argument("--chunk-size", type=int, default=None, help="Override de chunk_size.")
    ap.add_argument("--chunk-overlap", type=int, default=None, help="Override de chunk_overlap.")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
        # Overrides de CLI (se revalida para respetar 0 <= overlap < size).
        if args.chunk_size is not None:
            cfg.chunk_size = args.chunk_size
        if args.chunk_overlap is not None:
            cfg.chunk_overlap = args.chunk_overlap
        cfg.validate()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Configuración: {exc}", file=sys.stderr)
        return 2

    try:
        return run(cfg)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
