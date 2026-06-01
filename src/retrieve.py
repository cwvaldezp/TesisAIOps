"""
retrieve.py — CLI de recuperación top-k (ADR-014, Fase 3).

PROPÓSITO
    Punto de entrada para consultar el índice: recibe una consulta textual, la
    embebe (mismo modelo local), busca top-k en Chroma con filtros opcionales y
    muestra los chunks recuperados con score y cita. SOLO recuperación: NO LLM,
    NO RAG generativo, NO interfaz web.

CUÁNDO / QUIÉN LO INVOCA
    Manualmente:
        python -m src.retrieve "errores 503 backend down"
        python -m src.retrieve "latencia alta" --top-k 3 --severity error
        python -m src.retrieve "..." --source haproxy_sample.log --json

ENTRADAS
    config/config.yaml (sección `retrieval`/`vector_store`/`embeddings`) + consulta.

SALIDAS
    Lista de resultados por consola (texto o JSON). Código de salida 0 si ok.

DEPENDENCIAS
    src.config, src.embedder (modelo local), src.vector_store (Chroma),
    src.retriever (lógica). Carga el modelo y Chroma al ejecutar.

RIESGOS
    - Índice vacío / sin coincidencias -> se informa, exit 0.
    - chromadb o modelo no disponibles -> error claro (exit 3).

IMPACTO DE CAMBIOS
    Parámetros desde config (ADR-014). NUNCA toca infraestructura (ADR-005): solo
    lee el índice local y calcula.
"""

from __future__ import annotations

import argparse
import json
import sys

from src.config import Config, load_config
from src.embedder import Embedder
from src.retriever import build_where, retrieve
from src.vector_store import ChromaVectorStore


def format_text(query: str, results: list[dict]) -> str:
    """Formatea los resultados como texto legible con cita."""
    if not results:
        return f'Consulta: "{query}"\n(sin coincidencias)'
    lineas = [f'Consulta: "{query}"  ·  {len(results)} resultado(s)', "-" * 60]
    for r in results:
        sev = ", ".join(f"{k}:{v}" for k, v in r["severities"].items()) or "-"
        lineas.append(
            f"#{r['rank']}  score={r['score']:.4f}  {r['document']}\n"
            f"     chunk={r['chunk_id']}  líneas {r['line_start']}-{r['line_end']}"
            f"  ts={r['ts_start']}..{r['ts_end']}  severidades=[{sev}]"
        )
    return "\n".join(lineas)


def run(cfg: Config, query: str, *, source=None, severity=None, as_json=False, store=None, embedder=None) -> int:
    """Ejecuta la recuperación. `store`/`embedder` son inyectables (tests)."""
    where = build_where(source=source, severity=severity)

    # En producción: modelo local + Chroma. En tests: fakes inyectados.
    if embedder is None:
        embedder = Embedder(model_name=cfg.embedding_model, batch_size=cfg.embedding_batch_size)
    if store is None:
        store = ChromaVectorStore(
            index_path=cfg.index_path,
            collection_name=cfg.collection_name,
            similarity_metric=cfg.similarity_metric,
        )

    results = retrieve(
        query,
        embed_fn=embedder.encode,
        store=store,
        top_k=cfg.top_k,
        where=where,
        metric=cfg.similarity_metric,
        score_threshold=cfg.score_threshold,
    )

    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(format_text(query, results))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI."""
    ap = argparse.ArgumentParser(
        description="Recuperación top-k sobre Chroma (ADR-014). Solo recupera (sin LLM)."
    )
    ap.add_argument("query", help="Consulta textual (entre comillas).")
    ap.add_argument("--config", default="config/config.yaml", help="Ruta al YAML.")
    ap.add_argument("--top-k", type=int, default=None, help="Override de top_k.")
    ap.add_argument("--source", default=None, help="Filtro: source_file exacto.")
    ap.add_argument(
        "--severity", choices=["info", "warning", "error"], default=None,
        help="Filtro: chunks con al menos un evento de esa severidad.",
    )
    ap.add_argument("--json", dest="as_json", action="store_true", help="Salida en JSON.")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
        if args.top_k is not None:
            cfg.top_k = args.top_k
        cfg.validate()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Configuración: {exc}", file=sys.stderr)
        return 2

    try:
        return run(cfg, args.query, source=args.source, severity=args.severity, as_json=args.as_json)
    except (ImportError, ValueError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
