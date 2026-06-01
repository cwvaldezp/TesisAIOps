"""
embedder.py — Convierte el texto de los chunks en vectores (ADR-012, Fase 2C).

PROPÓSITO
    Generar embeddings LOCALES del `text` de cada chunk con sentence-transformers
    (modelo `all-MiniLM-L6-v2`, 384-d) y combinarlos con los metadatos de
    citabilidad del chunk. NO indexa en Chroma ni hace RAG (fases posteriores).

ENTRADAS
    - chunks: lista de chunks (dicts con al menos `chunk_id` y `text`).
    - una función de codificación `encode_fn(textos) -> list[vector]`.
    - model_name: nombre del modelo (para registrarlo en cada vector).

SALIDAS
    Lista de "registros de embedding": dicts con `embedding` + `embedding_model` +
    `embedding_dim` + metadatos heredados del chunk (esquema en flujos §2.3).

DEPENDENCIAS
    sentence-transformers (solo al cargar el modelo real, import perezoso). La
    lógica de orquestación (`embed_chunks`, `build_embedding_record`) NO importa
    la librería: recibe la función de codificación inyectada, lo que permite
    probarla sin descargar ni cargar el modelo.

RIESGOS
    - Modelo no instalado o sin red la 1ª vez -> ImportError/RuntimeError claro.
    - Es solo lectura/cómputo local: no toca infraestructura (ADR-005).

IMPACTO DE CAMBIOS
    Cambiar `embedding_model` cambia la dimensión y la semántica del vector y
    obliga a reindexar en fases siguientes.
"""

from __future__ import annotations

from typing import Any, Callable

# Tipo de la función de codificación: recibe textos, devuelve un vector por texto.
EncodeFn = Callable[[list[str]], list[list[float]]]

# Orden canónico de las claves del registro de embedding (salida estable).
EMBEDDING_RECORD_FIELDS = (
    "chunk_id",
    "embedding",
    "embedding_model",
    "embedding_dim",
    "source_file",
    "line_start",
    "line_end",
    "ts_start",
    "ts_end",
    "severities",
)


class Embedder:
    """Envoltorio del modelo local de embeddings. Carga perezosa del modelo.

    Se usa en producción (CLI). En tests se inyecta una `encode_fn` falsa, por lo
    que esta clase (y su dependencia pesada) no es necesaria para probar la lógica.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None  # se carga en load() (perezoso)

    def load(self) -> "Embedder":
        """Carga el modelo (import perezoso de sentence-transformers)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - depende del entorno
                raise ImportError(
                    "sentence-transformers no está instalado. Instálelo "
                    "(pip install sentence-transformers) para usar el Embedder real."
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self

    @property
    def dim(self) -> int:
        """Dimensión del vector del modelo cargado.

        Soporta el nombre nuevo (`get_embedding_dimension`) y el antiguo
        (`get_sentence_embedding_dimension`) según la versión instalada.
        """
        self.load()
        getter = getattr(self._model, "get_embedding_dimension", None) or \
            self._model.get_sentence_embedding_dimension
        return int(getter())

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Codifica una lista de textos a vectores (lista de listas de float)."""
        self.load()
        vectors = self._model.encode(
            texts, batch_size=self.batch_size, convert_to_numpy=True
        )
        # Convierte cada fila numpy a lista de float nativos (serializable a JSON).
        return [[float(x) for x in row] for row in vectors]


def build_embedding_record(
    chunk: dict[str, Any], vector: list[float], model_name: str
) -> dict[str, Any]:
    """Combina un vector con los metadatos de citabilidad/filtrado de su chunk.

    No depende del modelo: es lógica pura y testeable.
    """
    record = {
        "chunk_id": chunk.get("chunk_id"),
        "embedding": vector,
        "embedding_model": model_name,
        "embedding_dim": len(vector),
        "source_file": chunk.get("source_file"),
        "line_start": chunk.get("line_start"),
        "line_end": chunk.get("line_end"),
        "ts_start": chunk.get("ts_start"),
        "ts_end": chunk.get("ts_end"),
        "severities": chunk.get("severities", {}),
    }
    return {k: record[k] for k in EMBEDDING_RECORD_FIELDS}


def embed_chunks(
    chunks: list[dict[str, Any]],
    *,
    encode_fn: EncodeFn,
    model_name: str,
) -> list[dict[str, Any]]:
    """Genera los registros de embedding para una lista de chunks.

    `encode_fn` se inyecta (Embedder.encode en producción; una función falsa en
    tests), de modo que esta función no carga ningún modelo por sí misma.
    """
    if not chunks:
        return []
    texts = [c.get("text", "") or "" for c in chunks]
    vectors = encode_fn(texts)
    if len(vectors) != len(chunks):
        raise ValueError(
            f"encode_fn devolvió {len(vectors)} vectores para {len(chunks)} chunks."
        )
    return [
        build_embedding_record(chunk, vector, model_name)
        for chunk, vector in zip(chunks, vectors)
    ]
