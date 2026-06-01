"""
embed_chunks.py — Orquestador CLI del Embedder (ADR-012, Fase 2C).

PROPÓSITO
    Pega el subflujo de embeddings (docs/03_flujos.md §2.3):
    1) localiza los `*.chunks.jsonl` en processed_path,
    2) carga los chunks,
    3) carga el modelo local de embeddings (una vez),
    4) vectoriza el `text` de cada chunk y lo combina con sus metadatos,
    5) escribe `<stem>.embeddings.jsonl` por cada archivo de chunks,
    6) imprime un resumen.

CUÁNDO / QUIÉN LO INVOCA
    Manualmente, tras el chunker, como paso offline de solo lectura:
        python -m src.embed_chunks
        python -m src.embed_chunks --model all-MiniLM-L6-v2

ENTRADAS
    config/config.yaml (sección `embeddings`) + archivos `*.chunks.jsonl`.

SALIDAS
    Un archivo `<stem>.embeddings.jsonl` por archivo de chunks, en processed_path,
    + resumen por consola. Código de salida 0 si todo fue bien.

DEPENDENCIAS
    src.config, src.embedder (este último carga sentence-transformers al ejecutar).
    NO indexa en Chroma ni hace RAG.

RIESGOS
    - Sin `*.chunks.jsonl` -> error claro y aborta.
    - Modelo no disponible (sin instalar / sin red la 1ª vez) -> error claro.

IMPACTO DE CAMBIOS
    Parámetros desde la config (ADR-012, ver docs/04). Cambiar el modelo obliga a
    reindexar. NUNCA toca infraestructura (ADR-005).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.config import Config, load_config
from src.embedder import Embedder, embed_chunks

CHUNKS_SUFFIX = ".chunks.jsonl"
EMBEDDINGS_SUFFIX = ".embeddings.jsonl"


def load_chunks(path: Path) -> list[dict[str, Any]]:
    """Carga un archivo JSONL de chunks (un objeto por línea)."""
    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido en {path.name}:{i} -> {exc}") from exc
    return chunks


def write_records(records: list[dict[str, Any]], out_path: Path) -> None:
    """Escribe los registros de embedding como JSONL."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(cfg: Config) -> int:
    """Ejecuta el embedding sobre todos los `*.chunks.jsonl`. Devuelve exit code."""
    processed_dir = Path(cfg.processed_path)
    if not processed_dir.exists():
        print(f"[ERROR] No existe processed_path: {processed_dir}", file=sys.stderr)
        return 1

    files = sorted(processed_dir.glob(f"*{CHUNKS_SUFFIX}"))
    if not files:
        print(
            f"[ERROR] No hay archivos '*{CHUNKS_SUFFIX}' en {processed_dir}. "
            "Ejecute antes el chunker (python -m src.chunk_logs).",
            file=sys.stderr,
        )
        return 1

    print("== TesisAIOps · Embedder (Fase 2C, ADR-012) ==")
    print(f"Carpeta        : {processed_dir}")
    print(f"Modelo (local) : {cfg.embedding_model}  batch={cfg.embedding_batch_size}")
    print("Cargando modelo (puede descargarlo la primera vez)...")

    # Carga el modelo una sola vez y reutiliza su función de codificación.
    embedder = Embedder(
        model_name=cfg.embedding_model, batch_size=cfg.embedding_batch_size
    ).load()
    print(f"Modelo cargado. Dimensión = {embedder.dim}")
    print("-" * 60)

    total = 0
    for path in files:
        stem = path.name[: -len(CHUNKS_SUFFIX)]
        chunks = load_chunks(path)
        records = embed_chunks(
            chunks, encode_fn=embedder.encode, model_name=cfg.embedding_model
        )
        out_path = processed_dir / f"{stem}{EMBEDDINGS_SUFFIX}"
        write_records(records, out_path)
        total += len(records)
        print(f"{path.name:30} chunks={len(chunks):3}  embeddings={len(records):3}  -> {out_path.name}")

    print("-" * 60)
    print(f"TOTAL: {len(files)} archivo(s), {total} embedding(s) escritos (dim={embedder.dim}).")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI. Permite override del modelo."""
    ap = argparse.ArgumentParser(
        description="Embedder: *.chunks.jsonl -> *.embeddings.jsonl (ADR-012, local)."
    )
    ap.add_argument("--config", default="config/config.yaml", help="Ruta al YAML.")
    ap.add_argument("--model", default=None, help="Override del modelo de embeddings.")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
        if args.model is not None:
            cfg.embedding_model = args.model
        cfg.validate()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Configuración: {exc}", file=sys.stderr)
        return 2

    try:
        return run(cfg)
    except (ImportError, ValueError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
