"""
Paquete `src` de TesisAIOps.

Contiene la lógica del MVP. En la Fase 1 solo incluye el subsistema de PARSING:
    - config.py          : carga de configuración (ADR-008)
    - schema.py          : esquema normalizado común (ADR-003)
    - parsers/           : parsers específicos por fuente (HAProxy, IIS)
    - parse_logs.py      : orquestador CLI del parser

Las fases posteriores (chunking, embeddings, vector store, retriever, LLM) NO
están implementadas todavía, por diseño (ver docs/00_vision_general.md, roadmap).
"""

__version__ = "0.1.0"  # Fase 1: parser
