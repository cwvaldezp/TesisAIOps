"""
validate_corpus.py — Arnés de validación del pipeline con CORPUS REAL (Fase 3.5).

QUÉ HACE
    Ejecuta el pipeline de indexación de extremo a extremo sobre archivos de log
    reales y **mide** cada etapa, SIN LLM:
        parse (HAProxy) -> chunking (ADR-011) -> embeddings (ADR-012)
        -> índice Chroma (ADR-013)
    Reporta por archivo y en total: nº de líneas, eventos, chunks, embeddings y
    los TIEMPOS de cada etapa (con foco en el tiempo de indexación).

CUÁNDO SE INVOCA
    Manualmente, como medición offline de solo lectura sobre el corpus real:
        python -m src.validate_corpus data/logs/api-account-devl/api-account-devl.usfq.edu.ec.log ...
        python -m src.validate_corpus            # (sin archivos) descubre por config

ENTRADAS
    - Lista explícita de archivos (.log o .gz) O, si se omite, descubrimiento por
      config (logs_path + file_patterns + recursive).
    - config/config.yaml (chunking/embeddings/vector_store).

SALIDAS
    - Tabla de métricas por consola.
    - Reporte JSON reproducible en data/processed/corpus_validation.json.
    - Índice Chroma en una colección SEPARDA (default: '<collection>_validacion')
      para no contaminar el índice de demostración.

QUÉ PUEDE FALLAR
    - Archivo inexistente -> se informa y se omite.
    - sentence-transformers / chromadb no instalados -> error claro (la carga del
      modelo es la etapa más lenta y la primera vez descarga el modelo).

EFECTO DE PARÁMETROS
    chunk_size/overlap (ADR-011) cambian el nº de chunks; embedding_batch_size
    (ADR-012) afecta el tiempo de embedding. NUNCA toca infraestructura real
    (ADR-005): solo lee logs y escribe en data/ (índice y reporte).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from src.chunker import chunk_events
from src.config import Config, load_config
from src.embedder import Embedder
from src.ingest import discover_log_files
from src.parse_logs import parse_file
from src.vector_store import ChromaVectorStore, build_payload


def _resolve_files(cfg: Config, explicit: list[str]) -> list[Path]:
    """Resuelve la lista de archivos: explícitos o descubiertos por config."""
    if explicit:
        return [Path(p) for p in explicit]
    return discover_log_files(
        cfg.logs_path, cfg.effective_patterns(), recursive=cfg.recursive
    )


def process_file(
    path: Path, cfg: Config, embedder: Embedder, source: str
) -> dict[str, Any]:
    """Parsea, trocea y embebe un único archivo. Devuelve métricas + registros.

    Mide los tiempos de parse/chunk/embed por archivo. La indexación se hace
    en lote fuera de esta función (para medir el tiempo de indexación global).
    """
    t0 = time.perf_counter()
    events, stats = parse_file(path, cfg, forced_source=source)
    t_parse = time.perf_counter() - t0

    t0 = time.perf_counter()
    chunks = chunk_events(
        events,
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        stem=path.stem,
    )
    t_chunk = time.perf_counter() - t0

    t0 = time.perf_counter()
    records: list[dict[str, Any]] = []
    if chunks:
        from src.embedder import embed_chunks

        records = embed_chunks(
            chunks, encode_fn=embedder.encode, model_name=cfg.embedding_model
        )
    t_embed = time.perf_counter() - t0

    return {
        "file": path.name,
        "lines": stats["total"],
        "events": len(events),
        "chunks": len(chunks),
        "embeddings": len(records),
        "t_parse": round(t_parse, 3),
        "t_chunk": round(t_chunk, 3),
        "t_embed": round(t_embed, 3),
        "_records": records,
    }


def run(cfg: Config, files: list[Path], *, source: str, collection: str) -> dict[str, Any]:
    """Ejecuta la validación completa y devuelve el reporte de métricas."""
    # Carga del modelo de embeddings (etapa más lenta; la 1ª vez descarga ~80 MB).
    t0 = time.perf_counter()
    embedder = Embedder(
        model_name=cfg.embedding_model, batch_size=cfg.embedding_batch_size
    ).load()
    t_model_load = time.perf_counter() - t0

    per_file: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    for path in files:
        if not path.is_file():
            print(f"[AVISO] No existe, se omite: {path}", file=sys.stderr)
            continue
        m = process_file(path, cfg, embedder, source)
        all_records.extend(m.pop("_records"))
        per_file.append(m)
        print(
            f"  {m['file']:48} líneas={m['lines']:>6} eventos={m['events']:>6} "
            f"chunks={m['chunks']:>5} emb={m['embeddings']:>5} "
            f"(parse {m['t_parse']}s · chunk {m['t_chunk']}s · embed {m['t_embed']}s)"
        )

    # Indexación en Chroma (colección separada) — etapa medida aparte.
    store = ChromaVectorStore(
        index_path=cfg.index_path,
        collection_name=collection,
        similarity_metric=cfg.similarity_metric,
    )
    payload = build_payload(all_records)
    t0 = time.perf_counter()
    store.upsert(payload)
    t_index = time.perf_counter() - t0
    indexed_count = store.count()

    totals = {
        "files": len(per_file),
        "lines": sum(m["lines"] for m in per_file),
        "events": sum(m["events"] for m in per_file),
        "chunks": sum(m["chunks"] for m in per_file),
        "embeddings": sum(m["embeddings"] for m in per_file),
        "t_parse": round(sum(m["t_parse"] for m in per_file), 3),
        "t_chunk": round(sum(m["t_chunk"] for m in per_file), 3),
        "t_embed": round(sum(m["t_embed"] for m in per_file), 3),
        "t_model_load": round(t_model_load, 3),
        "t_index": round(t_index, 3),
        "indexed_count": indexed_count,
    }

    return {
        "source": source,
        "collection": collection,
        "embedding_model": cfg.embedding_model,
        "embedding_dim": embedder.dim,
        "chunk_size": cfg.chunk_size,
        "chunk_overlap": cfg.chunk_overlap,
        "per_file": per_file,
        "totals": totals,
    }


def print_summary(report: dict[str, Any]) -> None:
    """Imprime el resumen de totales de forma legible."""
    t = report["totals"]
    print("-" * 78)
    print(
        f"TOTAL: {t['files']} archivo(s) · {t['lines']} líneas · {t['events']} eventos · "
        f"{t['chunks']} chunks · {t['embeddings']} embeddings"
    )
    print(
        f"Tiempos: carga modelo {t['t_model_load']}s · parse {t['t_parse']}s · "
        f"chunk {t['t_chunk']}s · embed {t['t_embed']}s · "
        f"**indexación {t['t_index']}s** · puntos en índice={t['indexed_count']}"
    )
    print(
        f"Modelo: {report['embedding_model']} ({report['embedding_dim']}-d) · "
        f"chunk_size={report['chunk_size']} overlap={report['chunk_overlap']} · "
        f"colección='{report['collection']}'"
    )


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI."""
    ap = argparse.ArgumentParser(
        description="Valida el pipeline (parse->chunk->embed->index) con corpus real. Sin LLM."
    )
    ap.add_argument("files", nargs="*", help="Archivos de log (.log/.gz). Vacío = descubrir por config.")
    ap.add_argument("--config", default="config/config.yaml", help="Ruta al YAML.")
    ap.add_argument("--source", default="haproxy", choices=["auto", "haproxy", "iis"],
                    help="Fuente forzada (default haproxy: el corpus real es HAProxy).")
    ap.add_argument("--collection", default=None,
                    help="Colección Chroma (default: '<collection>_validacion').")
    ap.add_argument("--report", default="data/processed/corpus_validation.json",
                    help="Ruta del reporte JSON de métricas.")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Configuración: {exc}", file=sys.stderr)
        return 2

    files = _resolve_files(cfg, args.files)
    if not files:
        print("[ERROR] No hay archivos para validar.", file=sys.stderr)
        return 1

    collection = args.collection or f"{cfg.collection_name}_validacion"
    print(f"== TesisAIOps · Validación con corpus real (Fase 3.5) ==")
    print(f"Archivos: {len(files)} · fuente forzada: {args.source}")
    print("-" * 78)

    try:
        report = run(cfg, files, source=args.source, collection=collection)
    except (ImportError, ValueError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3

    print_summary(report)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f"\nReporte JSON: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
