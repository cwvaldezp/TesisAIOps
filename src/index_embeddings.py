"""
index_embeddings.py — Orquestador CLI de la indexación en Chroma (ADR-013, Fase 2D).

PROPÓSITO
    Pega el subflujo de indexación (docs/03_flujos.md §2.4):
    1) localiza los `*.embeddings.jsonl` en processed_path,
    2) carga los registros de embedding,
    3) construye el payload de Chroma (ids, embeddings, metadatos, documentos),
    4) hace upsert en la colección Chroma persistente,
    5) imprime el conteo final.
    SOLO indexa: NO consulta en lenguaje natural, NO RAG, NO LLM.

CUÁNDO / QUIÉN LO INVOCA
    Manualmente, tras el embedder, como paso offline de solo lectura de los
    embeddings (y escritura del índice local):
        python -m src.index_embeddings

ENTRADAS
    config/config.yaml (sección `vector_store`) + archivos `*.embeddings.jsonl`.

SALIDAS
    Colección Chroma persistida en `index_path` + resumen por consola.

DEPENDENCIAS
    src.config, src.vector_store (este último carga chromadb al ejecutar).

RIESGOS
    - Sin `*.embeddings.jsonl` -> error claro y aborta.
    - chromadb no disponible -> error claro.

IMPACTO DE CAMBIOS
    Parámetros desde la config (ADR-013, ver docs/04). Cambiar la métrica o el
    modelo de embeddings (dimensión) obliga a reconstruir. NUNCA toca
    infraestructura (ADR-005): solo lee archivos y escribe el índice local.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.config import Config, load_config
from src.vector_store import ChromaVectorStore, build_payload

EMBEDDINGS_SUFFIX = ".embeddings.jsonl"


def load_embedding_records(path: Path) -> list[dict[str, Any]]:
    """Carga un archivo JSONL de registros de embedding (uno por línea)."""
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido en {path.name}:{i} -> {exc}") from exc
    return records


def run(cfg: Config, store=None) -> int:
    """Indexa todos los `*.embeddings.jsonl`. `store` es inyectable (tests).

    Devuelve un código de salida (0 = ok).
    """
    processed_dir = Path(cfg.processed_path)
    if not processed_dir.exists():
        print(f"[ERROR] No existe processed_path: {processed_dir}", file=sys.stderr)
        return 1

    files = sorted(processed_dir.glob(f"*{EMBEDDINGS_SUFFIX}"))
    if not files:
        print(
            f"[ERROR] No hay archivos '*{EMBEDDINGS_SUFFIX}' en {processed_dir}. "
            "Ejecute antes el embedder (python -m src.embed_chunks).",
            file=sys.stderr,
        )
        return 1

    # En producción se usa Chroma; en tests se inyecta un store falso.
    if store is None:
        store = ChromaVectorStore(
            index_path=cfg.index_path,
            collection_name=cfg.collection_name,
            similarity_metric=cfg.similarity_metric,
        )

    print("== TesisAIOps · Vector store / indexación (Fase 2D, ADR-013) ==")
    print(f"Backend        : {cfg.vector_backend}")
    print(f"Índice         : {cfg.index_path}  colección='{cfg.collection_name}'  métrica={cfg.similarity_metric}")
    print("-" * 60)

    total_indexados = 0
    for path in files:
        records = load_embedding_records(path)
        payload = build_payload(records)
        store.upsert(payload)
        total_indexados += len(payload["ids"])
        print(f"{path.name:34} registros={len(records):3}  -> upsert OK")

    print("-" * 60)
    print(f"TOTAL: {total_indexados} punto(s) upsert. Colección ahora con {store.count()} punto(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI."""
    ap = argparse.ArgumentParser(
        description="Indexa *.embeddings.jsonl en Chroma (ADR-013). Solo indexa."
    )
    ap.add_argument("--config", default="config/config.yaml", help="Ruta al YAML.")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
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
