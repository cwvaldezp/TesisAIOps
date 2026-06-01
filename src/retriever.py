"""
retriever.py — Recuperación top-k sobre Chroma (ADR-014, Fase 3).

PROPÓSITO
    Dada una consulta textual, embeberla con el MISMO modelo local (ADR-012),
    buscar los top-k chunks más similares en Chroma (ADR-013) con filtros
    opcionales de metadatos, y devolver resultados ordenados con score y datos de
    cita. SOLO recuperación: NO ensambla prompt, NO llama a un LLM, NO genera
    respuestas (eso es Fase 4).

ENTRADAS
    - query: texto de la consulta.
    - embed_fn(textos) -> vectores (se inyecta Embedder.encode en producción).
    - store: objeto con `query(embedding, top_k, where)` (Chroma o un fake).
    - top_k, where (filtro de metadatos), metric, score_threshold.

SALIDAS
    Lista de resultados ordenados por score desc: dicts con rank, chunk_id, score,
    distance, document (cita), source_file, line_start/end, ts_*, severities.

DEPENDENCIAS
    Ninguna pesada: la lógica (build_results, distance_to_score, build_where) es
    pura y testeable sin chromadb ni el modelo. `embed_fn` y `store` se inyectan.

RIESGOS
    - Índice vacío -> lista vacía (no es error).
    - Un filtro demasiado estricto -> 0 resultados.

IMPACTO DE CAMBIOS
    `top_k`, `score_threshold` y los filtros cambian qué evidencia se recupera
    (precisión/recall). La métrica afecta la conversión distancia->score.
"""

from __future__ import annotations

from typing import Any, Callable

EncodeFn = Callable[[list[str]], list[list[float]]]

# Severidades conocidas (deben coincidir con el aplanado del vector store).
_SEVERITY_KEYS = ("info", "warning", "error")


def distance_to_score(distance: float, metric: str = "cosine") -> float:
    """Convierte una distancia de Chroma en un score de similitud (mayor = mejor).

    - cosine: score = 1 - distance (distancia coseno en [0, 2]).
    - otras métricas (l2, ip): fallback 1/(1+distance) (monótono decreciente).
    """
    if metric == "cosine":
        return 1.0 - distance
    return 1.0 / (1.0 + distance)


def reconstruct_severities(metadata: dict[str, Any]) -> dict[str, int]:
    """Reconstruye el dict de severidades desde los campos planos `sev_*`."""
    return {
        sev: int(metadata.get(f"sev_{sev}", 0) or 0)
        for sev in _SEVERITY_KEYS
        if int(metadata.get(f"sev_{sev}", 0) or 0) > 0
    }


def build_where(source: str | None = None, severity: str | None = None) -> dict | None:
    """Construye el filtro de metadatos `where` de Chroma desde flags simples.

    - source -> {"source_file": source}
    - severity in {info,warning,error} -> {"sev_<severity>": {"$gt": 0}}
    Combina ambos con $and. Devuelve None si no hay filtros.
    """
    clauses: list[dict] = []
    if source:
        clauses.append({"source_file": source})
    if severity:
        if severity not in _SEVERITY_KEYS:
            raise ValueError(f"severity inválida: {severity!r}. Use {list(_SEVERITY_KEYS)}.")
        clauses.append({f"sev_{severity}": {"$gt": 0}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def build_results(
    response: dict[str, list],
    *,
    metric: str = "cosine",
    score_threshold: float = 0.0,
) -> list[dict[str, Any]]:
    """Transforma la respuesta de Chroma en resultados ordenados y citables.

    Lógica pura (sin chromadb): testeable con una respuesta simulada.
    """
    ids = response.get("ids", [])
    distances = response.get("distances", [])
    metadatas = response.get("metadatas", [])
    documents = response.get("documents", [])

    results: list[dict[str, Any]] = []
    for i, chunk_id in enumerate(ids):
        distance = float(distances[i])
        score = distance_to_score(distance, metric)
        if score < score_threshold:
            continue
        md = metadatas[i] or {}
        results.append({
            "chunk_id": chunk_id,
            "score": round(score, 4),
            "distance": round(distance, 4),
            "document": documents[i] if i < len(documents) else None,
            "source_file": md.get("source_file"),
            "line_start": md.get("line_start"),
            "line_end": md.get("line_end"),
            "ts_start": md.get("ts_start") or None,
            "ts_end": md.get("ts_end") or None,
            "severities": reconstruct_severities(md),
        })

    # Ordena por score desc (Chroma ya viene ordenado, pero lo garantizamos) y
    # asigna el rank tras aplicar el umbral.
    results.sort(key=lambda r: r["score"], reverse=True)
    for rank, r in enumerate(results, start=1):
        r["rank"] = rank
    return results


def retrieve(
    query: str,
    *,
    embed_fn: EncodeFn,
    store: Any,
    top_k: int = 5,
    where: dict | None = None,
    metric: str = "cosine",
    score_threshold: float = 0.0,
) -> list[dict[str, Any]]:
    """Recupera los top-k chunks relevantes para `query`.

    `embed_fn` y `store` se inyectan: en producción son Embedder.encode y
    ChromaVectorStore; en tests, fakes (sin modelo ni chromadb).
    """
    if not query or not query.strip():
        raise ValueError("La consulta no puede estar vacía.")
    query_vector = embed_fn([query])[0]
    response = store.query(query_vector, top_k, where)
    return build_results(response, metric=metric, score_threshold=score_threshold)
