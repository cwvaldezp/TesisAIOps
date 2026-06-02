"""
config.py — Carga de la configuración del proyecto (ADR-008).

QUÉ HACE
    Lee `config/config.yaml` (parámetros no sensibles, versionables) y lo expone
    como un diccionario validado, con valores por defecto seguros. Los secretos
    NO se cargan aquí (irían en config/.env en fases futuras).

CUÁNDO SE INVOCA
    Al inicio del orquestador del parser (src/parse_logs.py) y en las pruebas.

ENTRADAS
    Ruta al archivo YAML (por defecto: config/config.yaml).

SALIDAS
    Un objeto `Config` con acceso por secciones (ingesta, parsing, etc.).

QUÉ PUEDE FALLAR
    - Archivo inexistente -> FileNotFoundError con mensaje claro.
    - YAML mal formado     -> yaml.YAMLError.
    - Valor de enum inválido (p. ej. on_parse_error) -> ValueError.

EFECTO DE PARÁMETROS
    Cada parámetro está documentado en docs/04_parametros_configuracion.md.
    Cambiarlos altera qué se lee, cómo se parsea y dónde se escribe la salida.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Ruta por defecto del archivo de configuración (relativa a la raíz del repo).
DEFAULT_CONFIG_PATH = Path("config/config.yaml")

# Valores permitidos para parámetros de tipo enumerado (se validan al cargar).
VALID_SOURCE_TYPE = {"auto", "haproxy", "iis"}
VALID_ON_PARSE_ERROR = {"skip", "keep", "fail"}
VALID_OUTPUT_FORMAT = {"json", "jsonl"}
# Estrategias de chunking soportadas (ADR-011). 'by_time' está previsto pero
# aún NO implementado en la Fase 2B.
VALID_CHUNK_STRATEGY = {"by_events"}
# Backends de vector store soportados (ADR-013). Solo Chroma en el MVP.
VALID_VECTOR_BACKEND = {"chroma"}
# Métricas de similitud soportadas por Chroma.
VALID_SIMILARITY_METRIC = {"cosine", "l2", "ip"}


@dataclass
class Config:
    """Configuración tipada del parser (subconjunto necesario para la Fase 1)."""

    # --- Ingesta ---
    logs_path: str = "./data/logs"
    file_pattern: str = "*.log"
    # Fase 3.5: corpus real organizado en subcarpetas por app y con .gz rotados.
    file_patterns: list[str] = field(default_factory=list)  # vacío -> [file_pattern]
    recursive: bool = False  # True -> explora subcarpetas (rglob)
    encoding: str = "utf-8"
    source_type: str = "auto"

    # --- Parsing ---
    haproxy_log_format: str = "http"
    iis_fields_from_header: bool = True
    iis_fields: list[str] = field(default_factory=list)
    on_parse_error: str = "skip"

    # --- Normalización ---
    timezone: str = "UTC"

    # --- Salida ---
    processed_path: str = "./data/processed"
    parser_output_format: str = "jsonl"

    # --- Chunking (ADR-011, Fase 2B) ---
    chunk_strategy: str = "by_events"
    chunk_size: int = 20
    chunk_overlap: int = 4

    # --- Embeddings (ADR-012, Fase 2C) ---
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 32

    # --- Vector store (ADR-013, Fase 2D) ---
    vector_backend: str = "chroma"
    index_path: str = "./data/index"
    similarity_metric: str = "cosine"
    collection_name: str = "tesisaiops"

    # --- Recuperación / Retriever (ADR-014, Fase 3) ---
    top_k: int = 5
    score_threshold: float = 0.0

    # --- Seguridad ---
    read_only: bool = True

    def validate(self) -> None:
        """Valida los enums; lanza ValueError con un mensaje accionable."""
        if self.source_type not in VALID_SOURCE_TYPE:
            raise ValueError(
                f"source_type inválido: {self.source_type!r}. "
                f"Use uno de {sorted(VALID_SOURCE_TYPE)}."
            )
        if self.on_parse_error not in VALID_ON_PARSE_ERROR:
            raise ValueError(
                f"on_parse_error inválido: {self.on_parse_error!r}. "
                f"Use uno de {sorted(VALID_ON_PARSE_ERROR)}."
            )
        if self.parser_output_format not in VALID_OUTPUT_FORMAT:
            raise ValueError(
                f"parser_output_format inválido: {self.parser_output_format!r}. "
                f"Use uno de {sorted(VALID_OUTPUT_FORMAT)}."
            )
        # --- Chunking (ADR-011) ---
        if self.chunk_strategy not in VALID_CHUNK_STRATEGY:
            raise ValueError(
                f"chunk_strategy inválido: {self.chunk_strategy!r}. "
                f"Soportado(s): {sorted(VALID_CHUNK_STRATEGY)} (by_time aún no implementado)."
            )
        if self.chunk_size <= 0:
            raise ValueError(f"chunk_size debe ser > 0 (es {self.chunk_size}).")
        if not (0 <= self.chunk_overlap < self.chunk_size):
            raise ValueError(
                f"chunk_overlap debe cumplir 0 <= overlap < chunk_size "
                f"(overlap={self.chunk_overlap}, chunk_size={self.chunk_size})."
            )
        # --- Embeddings (ADR-012) ---
        if self.embedding_batch_size <= 0:
            raise ValueError(
                f"embedding_batch_size debe ser > 0 (es {self.embedding_batch_size})."
            )
        # --- Vector store (ADR-013) ---
        if self.vector_backend not in VALID_VECTOR_BACKEND:
            raise ValueError(
                f"vector_backend inválido: {self.vector_backend!r}. "
                f"Soportado(s): {sorted(VALID_VECTOR_BACKEND)}."
            )
        if self.similarity_metric not in VALID_SIMILARITY_METRIC:
            raise ValueError(
                f"similarity_metric inválido: {self.similarity_metric!r}. "
                f"Use uno de {sorted(VALID_SIMILARITY_METRIC)}."
            )
        # --- Recuperación (ADR-014) ---
        if self.top_k <= 0:
            raise ValueError(f"top_k debe ser > 0 (es {self.top_k}).")
        if not (0.0 <= self.score_threshold <= 1.0):
            raise ValueError(
                f"score_threshold debe estar en [0.0, 1.0] (es {self.score_threshold})."
            )
        # Invariante de seguridad del MVP (ADR-005): el parser es solo lectura.
        if self.read_only is not True:
            raise ValueError(
                "read_only debe ser true: el MVP nunca actúa sobre infraestructura "
                "(invariante ADR-005)."
            )

    def effective_patterns(self) -> list[str]:
        """Patrones glob efectivos para descubrir logs (Fase 3.5).

        Usa `file_patterns` si está definido (lista); si no, cae al
        `file_pattern` único (compatibilidad con la config de Fase 1).
        """
        return list(self.file_patterns) if self.file_patterns else [self.file_pattern]


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    """Devuelve una sección del YAML como dict (vacío si falta)."""
    value = data.get(name) or {}
    if not isinstance(value, dict):
        raise ValueError(f"La sección '{name}' del config debe ser un mapeo.")
    return value


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Config:
    """Carga y valida la configuración desde un archivo YAML.

    Si una clave falta en el YAML, se usa el valor por defecto del dataclass.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración: {path}. "
            "Cópielo/ajústelo a partir de config/config.yaml."
        )

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    ingesta = _section(data, "ingesta")
    parsing = _section(data, "parsing")
    normalizacion = _section(data, "normalizacion")
    salida = _section(data, "salida")
    chunking = _section(data, "chunking")
    embeddings = _section(data, "embeddings")
    vector_store = _section(data, "vector_store")
    retrieval = _section(data, "retrieval")
    seguridad = _section(data, "seguridad")

    cfg = Config(
        logs_path=ingesta.get("logs_path", Config.logs_path),
        file_pattern=ingesta.get("file_pattern", Config.file_pattern),
        file_patterns=ingesta.get("file_patterns", []),
        recursive=ingesta.get("recursive", Config.recursive),
        encoding=ingesta.get("encoding", Config.encoding),
        source_type=ingesta.get("source_type", Config.source_type),
        haproxy_log_format=parsing.get("haproxy_log_format", Config.haproxy_log_format),
        iis_fields_from_header=parsing.get(
            "iis_fields_from_header", Config.iis_fields_from_header
        ),
        iis_fields=parsing.get("iis_fields", []),
        on_parse_error=parsing.get("on_parse_error", Config.on_parse_error),
        timezone=normalizacion.get("timezone", Config.timezone),
        processed_path=salida.get("processed_path", Config.processed_path),
        parser_output_format=salida.get(
            "parser_output_format", Config.parser_output_format
        ),
        chunk_strategy=chunking.get("chunk_strategy", Config.chunk_strategy),
        chunk_size=chunking.get("chunk_size", Config.chunk_size),
        chunk_overlap=chunking.get("chunk_overlap", Config.chunk_overlap),
        embedding_model=embeddings.get("embedding_model", Config.embedding_model),
        embedding_batch_size=embeddings.get(
            "embedding_batch_size", Config.embedding_batch_size
        ),
        vector_backend=vector_store.get("vector_backend", Config.vector_backend),
        index_path=vector_store.get("index_path", Config.index_path),
        similarity_metric=vector_store.get("similarity_metric", Config.similarity_metric),
        collection_name=vector_store.get("collection_name", Config.collection_name),
        top_k=retrieval.get("top_k", Config.top_k),
        score_threshold=retrieval.get("score_threshold", Config.score_threshold),
        read_only=seguridad.get("read_only", Config.read_only),
    )
    cfg.validate()
    return cfg
