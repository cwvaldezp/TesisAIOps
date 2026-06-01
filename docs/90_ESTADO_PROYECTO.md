# 90 · Estado del proyecto (fotografía)

> Instantánea del estado de TesisAIOps en una fecha concreta. Sirve para retomar
> el proyecto tras una pausa sabiendo **exactamente** dónde quedó. Se actualiza al
> cerrar cada fase/sub-fase.

---

## Resumen

| Campo | Valor |
|---|---|
| **Fecha de la foto** | 2026-06-01 |
| **Versión (paquete)** | `0.1.0` (`src/__init__.py`) · **hito: Fase 3 cerrada** |
| **Rama** | `main` (sincronizada con `origin/main`) |
| **Remoto** | https://github.com/cwvaldezp/TesisAIOps.git |
| **Estado global** | 🟢 **Recuperación de evidencia FUNCIONAL**: parseo → normalización → chunking → embeddings → índice **Chroma** → **Retriever top-k + filtros (CLI)**. Consulta textual operativa; **sin RAG generativo, sin LLM**. |
| **Próximo objetivo** | **Fase 4 — Capa LLM (respuesta con citas, RF-09/10/11)** |
| **Hito siguiente previsto** | **Fase 4 — LLM + respuesta con citas** (requiere decidir el modelo LLM vía ADR) |

> **Versión:** se mantiene **`__version__ = "0.1.0"`** de forma deliberada (no se
> sube a 0.2.0 en este hito). El avance de fase se rastrea por esta fotografía y
> por la bitácora de ADR, no por el número de versión del paquete.

---

## Fases completadas

| Fase | Descripción | Entregable | Estado |
|------|-------------|-----------|--------|
| 0 | Estructura + documentación base | README + `docs/00–07,98,99` + diagramas | ✅ |
| 1.0 | Parser base HAProxy/IIS + salida JSON/JSONL | `src/parsers/`, `src/parse_logs.py` | ✅ |
| 1.1 | Esquema normalizado (contrato 13 campos) | ADR-010, `src/schema.py` | ✅ |
| 1.2 | Conformidad ADR-010 HAProxy + demo | `tests/test_adr010_conformance.py`, `examples/` | ✅ |
| 1.3 | Conformidad ADR-010 IIS · **Fase 1 cerrada** | tests de conformidad IIS | ✅ |
| 2A | Diseño IA (chunking/embeddings/vector store/recuperación) | ADR-011, 012, 013, 014 | ✅ (diseño) |
| 2B | Chunker (stdlib, sin IA) | `src/chunker.py`, `src/chunk_logs.py` | ✅ |
| 2C | Embedder (sentence-transformers local, 384-d) | `src/embedder.py`, `src/embed_chunks.py` | ✅ |
| 2D | Vector store Chroma (local persistente, upsert) | `src/vector_store.py`, `src/index_embeddings.py` | ✅ |
| 3 | Retriever (recuperación top-k + filtros, **sin LLM**) | `src/retriever.py`, `src/retrieve.py` | ✅ |

**Flujos demostrables hoy:**
- `log (HAProxy/IIS) → parse_line() → evento normalizado (13 campos) → JSON`
- `*.events.jsonl → Chunker → *.chunks.jsonl`
- `*.chunks.jsonl → Embedder → *.embeddings.jsonl` (embeddings + metadata)
- `*.embeddings.jsonl → Chroma (data/index/)` (índice citable y filtrable)
- `consulta textual → Retriever → top-k chunks con score + cita` (`python -m src.retrieve "..."`, **sin LLM**)

## Fases pendientes

| Fase | Descripción | Requisito(s) | ADR | Prerrequisito |
|------|-------------|--------------|-----|---------------|
| **4** | **Capa LLM (respuesta con citas)** | RF-09, RF-10, RF-11 | _(pendiente ADR)_ | Decidir modelo LLM |
| 5 | Interfaz de consulta + demo | RF-12 | ADR-006 | — |

## ADRs cerrados (14)

| ADR | Decisión | Estado |
|-----|----------|--------|
| 001 | Arquitectura RAG (no LLM puro) | Aceptada |
| 002 | Separar pipelines indexación/consulta | Aceptada |
| 003 | Esquema común HAProxy/IIS | Aceptada |
| 004 | Documentación primero (doc-driven) | Aceptada |
| 005 | MVP solo-lectura (sin infraestructura) | Aceptada |
| 006 | CLI antes que web | Aceptada |
| 007 | Externalizar parámetros | Aceptada |
| 008 | Configuración YAML + `.env` | Aceptada |
| 009 | Revisión multi-rol + Definition of Done | Aceptada |
| 010 | Esquema de evento (13 campos) | Aceptada · **implementado** |
| 011 | Chunking por ventana de eventos | Aceptada · **implementado (2B)** |
| 012 | Embeddings locales (MiniLM) | Aceptada · **implementado (2C)** |
| 013 | Vector store Chroma | Aceptada · **implementado (2D)** |
| 014 | Recuperación top-k + filtros | Aceptada · **implementado (3)** |

> Pendiente de decisión (sin ADR aún): **modelo LLM** (Fase 4).

## Preguntas de defensa (27)

`P-01 … P-27` en [`98_PREGUNTAS_DEFENSA.md`](98_PREGUNTAS_DEFENSA.md), en formato
tribunal (7 facetas a partir de R16). Cobertura por tema:

| Rango | Tema |
|-------|------|
| P-01..P-07 | Decisiones de arquitectura (RAG, pipelines, esquema, doc-first, solo-lectura, CLI, config) |
| P-08..P-10 | Detalle del parser (citabilidad, stdlib, severidad) |
| P-11 | Vector store (cerrada → ADR-013/P-21) |
| P-12 | Metodología de revisión multi-rol |
| P-13..P-17 | Esquema normalizado y conformidad ADR-010 (HAProxy/IIS) |
| P-18 | Normalización **antes** que IA |
| P-19..P-23 | Decisiones de Fase 2A (chunking, embeddings, Chroma vs FAISS, recuperación) |
| P-24 | Diseño del chunker (agrupación por archivo + metadatos) |
| P-25 | Cómo se prueba el Embedder sin el modelo real (inyección de `encode_fn`) |
| P-26 | Metadatos en Chroma (aplanado) y upsert idempotente |
| P-27 | Consulta textual → evidencia recuperada **sin LLM** (Retriever, Fase 3) |

## Métricas actuales

| Métrica | Valor |
|---|---|
| Pruebas (pytest) | **66 / 66 en verde** |
| Archivos de prueba | 12 (`tests/test_*.py`) |
| Módulos Python (`src/`) | 16 (incluye `src/retriever.py`, `src/retrieve.py`) |
| Scripts de ejemplo | 1 (`examples/demo_haproxy_parser.py`) |
| Documentos (`docs/`) | 13 `.md` + 3 diagramas `.mmd` |
| ADRs | 14 |
| Preguntas de defensa | 27 |
| Requisitos funcionales cumplidos | RF-01…RF-08 (8 / 12) |
| Commits | 5 |
| Dependencias externas | PyYAML, pytest, sentence-transformers, chromadb (**sin nuevas en Fase 3**) |

**Cobertura de requisitos funcionales:**

| RF | Descripción | Estado |
|----|-------------|--------|
| RF-01 | Ingerir HAProxy | ✅ |
| RF-02 | Ingerir IIS | ✅ |
| RF-03 | Normalizar a esquema común | ✅ |
| RF-04 | Chunking | ✅ |
| RF-05 | Embeddings | ✅ |
| RF-06 | Indexar (vector store) | ✅ |
| RF-07 | Consulta en lenguaje natural | ✅ (CLI `src/retrieve.py`) |
| RF-08 | Recuperar chunks | ✅ |
| RF-09 | Ensamblar contexto/prompt | 📋 |
| RF-10 | Generar respuesta (LLM) | 📋 |
| RF-11 | Citar líneas de log | 📋 |
| RF-12 | Interfaz de consulta | 📋 |

---

## Próximo objetivo: Fase 4 — Capa LLM (respuesta con citas)

**Qué:** sobre la evidencia que ya entrega el Retriever (Fase 3), **ensamblar el
contexto/prompt** (RF-09), **generar una respuesta con un LLM** (RF-10) y **citar
las líneas de log** que la sustentan (RF-11). Cierra el ciclo RAG completo.

**Por qué ahora:** la recuperación de evidencia ya funciona y es citable; el
siguiente paso natural es convertir esos chunks en una respuesta auditable.

**Prerrequisito (bloqueante):** **decidir el modelo LLM** mediante un ADR nuevo
(local vs API; calidad vs coste vs privacidad). Sin esa decisión no se implementa.

**Riesgos / notas:**
- La elección local vs API tensiona privacidad (espíritu ADR-005) contra calidad.
- Las citas deben anclarse a los metadatos del chunk (RNF-05) para evitar alucinación.

**Estado de Fase 3 (cerrada):** Retriever top-k denso (coseno) con filtros de
metadatos operativo por CLI (`python -m src.retrieve "..."`); `embed_fn`/`store`
inyectables → tests sin modelo ni chromadb; **66 pruebas en verde** (P-27).

---

## Cómo regenerar esta fotografía

```bash
git rev-list --count HEAD                  # nº de commits
grep -c "^### ADR-" docs/05_bitacora_decisiones.md   # ADRs (resta 1: plantilla)
grep -c "^## P-"   docs/98_PREGUNTAS_DEFENSA.md       # preguntas de defensa
python -m pytest -q                        # nº de pruebas
```

> **Mantenimiento:** actualizar la **fecha**, las métricas y la tabla de fases al
> cerrar cada sub-fase (forma parte de la Definition of Done, R14).
