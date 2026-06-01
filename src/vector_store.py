"""
vector_store.py — Indexación de embeddings en Chroma (ADR-013, Fase 2D).

PROPÓSITO
    Cargar los registros de `*.embeddings.jsonl` en una colección Chroma local y
    persistente, guardando vector + metadatos de citabilidad/filtrado. SOLO
    escritura/indexación: NO consulta en lenguaje natural, NO RAG, NO LLM.

ENTRADAS
    - registros de embedding (dicts con `chunk_id`, `embedding`, metadatos).
    - parámetros: index_path, collection_name, similarity_metric.

SALIDAS
    Una colección Chroma persistida en `index_path` con un punto por chunk.

DEPENDENCIAS
    chromadb (solo en el envoltorio real, import perezoso). La transformación de
    registros a "payload de Chroma" es lógica pura (sin chromadb), por lo que se
    puede probar sin la librería.

RIESGOS
    - chromadb no instalado -> ImportError claro.
    - Metadatos no escalares -> Chroma los rechaza; por eso se APLANAN aquí.
    - Es solo lectura de archivos + escritura del índice local (ADR-005).

IMPACTO DE CAMBIOS
    Cambiar la métrica o la dimensión (modelo de embeddings) obliga a reconstruir
    la colección.
"""

from __future__ import annotations

from typing import Any

# Metadatos planos que se guardan por punto (Chroma solo admite escalares:
# str/int/float/bool — NO listas ni dicts).
def to_chroma_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Aplana los metadatos de un registro de embedding para Chroma.

    - `severities` (dict) -> sev_info / sev_warning / sev_error (int).
    - Los None se sustituyen por "" (Chroma no acepta None).
    """
    sev = record.get("severities") or {}
    def s(value: Any) -> Any:
        return "" if value is None else value
    return {
        "source_file": s(record.get("source_file")),
        "line_start": record.get("line_start") if record.get("line_start") is not None else -1,
        "line_end": record.get("line_end") if record.get("line_end") is not None else -1,
        "ts_start": s(record.get("ts_start")),
        "ts_end": s(record.get("ts_end")),
        "embedding_model": s(record.get("embedding_model")),
        "embedding_dim": record.get("embedding_dim") if record.get("embedding_dim") is not None else -1,
        "sev_info": int(sev.get("info", 0)),
        "sev_warning": int(sev.get("warning", 0)),
        "sev_error": int(sev.get("error", 0)),
    }


def to_chroma_document(record: dict[str, Any]) -> str:
    """Documento legible = referencia de cita 'archivo:linea_ini-linea_fin'."""
    return f"{record.get('source_file')}:{record.get('line_start')}-{record.get('line_end')}"


def build_payload(records: list[dict[str, Any]]) -> dict[str, list]:
    """Transforma registros de embedding en el payload de `collection.upsert`.

    Devuelve un dict con listas paralelas: ids, embeddings, metadatas, documents.
    Es lógica pura (sin chromadb) -> testeable sin la librería.
    """
    ids: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, Any]] = []
    documents: list[str] = []
    for r in records:
        ids.append(r["chunk_id"])
        embeddings.append(r["embedding"])
        metadatas.append(to_chroma_metadata(r))
        documents.append(to_chroma_document(r))
    return {
        "ids": ids,
        "embeddings": embeddings,
        "metadatas": metadatas,
        "documents": documents,
    }


class ChromaVectorStore:
    """Envoltorio mínimo de una colección Chroma persistente (import perezoso).

    En tests se inyecta un store falso con el mismo `upsert`/`count`, por lo que
    esta clase (y chromadb) no es necesaria para probar la lógica de payload.
    """

    def __init__(
        self,
        index_path: str = "./data/index",
        collection_name: str = "tesisaiops",
        similarity_metric: str = "cosine",
    ) -> None:
        self.index_path = index_path
        self.collection_name = collection_name
        self.similarity_metric = similarity_metric
        self._client = None
        self._collection = None

    def open(self) -> "ChromaVectorStore":
        """Abre (o crea) el cliente persistente y la colección."""
        if self._collection is None:
            try:
                import chromadb
            except ImportError as exc:  # pragma: no cover - depende del entorno
                raise ImportError(
                    "chromadb no está instalado. Instálelo (pip install chromadb) "
                    "para indexar en el vector store."
                ) from exc
            self._client = chromadb.PersistentClient(path=self.index_path)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.similarity_metric},
            )
        return self

    def upsert(self, payload: dict[str, list]) -> None:
        """Inserta/actualiza puntos por id (idempotente al reindexar)."""
        self.open()
        if not payload["ids"]:
            return
        self._collection.upsert(
            ids=payload["ids"],
            embeddings=payload["embeddings"],
            metadatas=payload["metadatas"],
            documents=payload["documents"],
        )

    def count(self) -> int:
        """Nº de puntos en la colección."""
        self.open()
        return int(self._collection.count())
