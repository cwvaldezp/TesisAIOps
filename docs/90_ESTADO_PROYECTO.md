# 90 · Estado del proyecto (fotografía)

> Instantánea del estado de TesisAIOps en una fecha concreta. Sirve para retomar
> el proyecto tras una pausa sabiendo **exactamente** dónde quedó. Se actualiza al
> cerrar cada fase/sub-fase.

---

## Resumen

| Campo | Valor |
|---|---|
| **Fecha de la foto** | 2026-06-02 |
| **Versión (paquete)** | `0.1.0` (`src/__init__.py`) · **hito: Retriever evaluado (tag `v0.6.0-retriever-evaluated`) · diseño Fase 4 listo (ADR-016/017)** |
| **Rama** | `main` (sincronizada con `origin/main`) |
| **Remoto** | https://github.com/cwvaldezp/TesisAIOps.git |
| **Estado global** | 🟢 **Pipeline VALIDADO con corpus real**: parseo → … → índice Chroma → Retriever, ejecutado sobre logs HAProxy reales (27 280 eventos, 1 706 chunks). **Sin RAG generativo, sin LLM**. |
| **Próximo objetivo** | **Fase 4B — implementar la Capa LLM** (Ollama + Qwen2.5 7B, RF-09/10/11) |
| **Hito siguiente previsto** | **Fase 4B — generación con citas** (instalar Ollama + `ollama pull qwen2.5`; **aún no hecho**) |

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
| 3.5 | Validación con corpus real HAProxy (`.gz`, cabeceras capturadas, medición) | `src/ingest.py`, `src/validate_corpus.py`, `docs/91_VALIDACION_CORPUS.md` | ✅ |
| 4A | Selección de modelo LLM (decisión, **sin código**) | ADR-016 (Ollama + Qwen2.5 7B) | ✅ (diseño) |

**Flujos demostrables hoy:**
- `log (HAProxy/IIS) → parse_line() → evento normalizado (13 campos) → JSON`
- `*.events.jsonl → Chunker → *.chunks.jsonl`
- `*.chunks.jsonl → Embedder → *.embeddings.jsonl` (embeddings + metadata)
- `*.embeddings.jsonl → Chroma (data/index/)` (índice citable y filtrable)
- `consulta textual → Retriever → top-k chunks con score + cita` (`python -m src.retrieve "..."`, **sin LLM**)

## Fases pendientes

| Fase | Descripción | Requisito(s) | ADR | Prerrequisito |
|------|-------------|--------------|-----|---------------|
| **4B** | **Capa LLM (respuesta con citas)** — implementación | RF-09, RF-10, RF-11 | ADR-016 | Instalar Ollama + `ollama pull qwen2.5` |
| 5 | Interfaz de consulta + demo | RF-12 | ADR-006 | — |

## ADRs cerrados (17)

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
| 015 | Corpus real: `.gz` + cabeceras capturadas + ingesta recursiva | Aceptada · **implementado (3.5)** |
| 016 | Modelo LLM: Ollama + Qwen2.5 7B (local) | **Aceptada (diseño)** — Fase 4A |
| 017 | Diseño capa LLM: prompt, anti-alucinación, citas, validación | **Aceptada (diseño)** — 4B · `docs/92` |

> Modelo LLM decidido en **ADR-016** (Fase 4A) y **diseño** de la capa LLM
> **aprobado** en **ADR-017** (+ `docs/92_DISENO_CAPA_LLM.md`), incluida la decisión
> de guardar el **texto del chunk como `document` de Chroma**. Sin decisiones de
> ADR pendientes; su **implementación** es la Fase 4B (aún no iniciada).

## Preguntas de defensa (33)

`P-01 … P-33` en [`98_PREGUNTAS_DEFENSA.md`](98_PREGUNTAS_DEFENSA.md), en formato
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
| P-28 | Validación con corpus real: desajustes vs. sintéticos (`.gz`, cabeceras capturadas) |
| P-29 | LLM **local** (Ollama + Qwen2.5) vs. API en la nube (privacidad/coste/repro) |
| P-30 | Citas **reales** y no alucinadas: tokens `[E#]` deterministas + validación |
| P-31 | Validación experimental del Retriever (recupera evidencia real relevante) |
| P-32 | Evaluación objetiva del Retriever (12 consultas, Precisión@1/@3) |
| P-33 | Análisis de fallos del Retriever: causa raíz y priorización de mejoras |

## Métricas actuales

| Métrica | Valor |
|---|---|
| Pruebas (pytest) | **73 / 73 en verde** |
| Archivos de prueba | 13 (`tests/test_*.py`) |
| Módulos Python (`src/`) | 18 (incluye `src/ingest.py`, `src/validate_corpus.py`) |
| Scripts de ejemplo | 1 (`examples/demo_haproxy_parser.py`) |
| Documentos (`docs/`) | 16 `.md` + 4 diagramas `.mmd` |
| ADRs | 17 (todos aceptados/implementados) |
| Preguntas de defensa | 33 |
| Requisitos funcionales cumplidos | RF-01…RF-08 (8 / 12) |
| Commits | 10 |
| Tags | 2 (`v0.5.0-retriever-validated`, `v0.6.0-retriever-evaluated`) |
| Dependencias externas | PyYAML, pytest, sentence-transformers, chromadb. **Prevista Fase 4B:** Ollama (runtime local, ADR-016) — aún **no instalado** |
| Validación corpus real | 27 280 eventos · 1 706 chunks · indexación 2,2 s (ver `91_VALIDACION_CORPUS.md`) |
| Validación Retriever | consulta real "errores 404…" → top-5 coherente, verificado vs. log real (ver `93_VALIDACION_RETRIEVER.md`) |
| Evaluación Retriever | 12 consultas · Precisión@1=0.42 (0.67 c/parciales) · Precisión@3=0.40 · Éxito@3=0.67 (ver `94_EVALUACION_RECUPERACION.md`) |
| Análisis de fallos | causa raíz: fallos duros 75 % ausencia / 25 % modelo; prioriza híbrido > re-ranking (ver `95_ANALISIS_FALLOS_RETRIEVER.md`) |

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

## Próximo objetivo: Fase 4B — implementar la Capa LLM (respuesta con citas)

**Qué:** sobre la evidencia que ya entrega el Retriever (Fase 3), **ensamblar el
contexto/prompt** (RF-09), **generar una respuesta con el LLM** (RF-10) y **citar
las líneas de log** que la sustentan (RF-11). Cierra el ciclo RAG completo.

**Modelo decidido (Fase 4A, ADR-016):** **Ollama + Qwen2.5 7B (local)**, con Llama
3.1 8B como alternativa documentada; capa agnóstica contra el endpoint
OpenAI-compatible de Ollama (`localhost:11434`). Razón: privacidad por diseño,
coste cero y reproducibilidad (P-29).

**Diseño de 4B (aprobado, sin código):** prompt, anti-alucinación, formato de
citas, flujo y métricas en **`docs/92_DISENO_CAPA_LLM.md`** + **ADR-017 (Aceptada)**
(+ diagrama `diagrams/flujo_llm_generacion.mmd`), incluida la decisión de guardar el
**texto del chunk como `document` de Chroma** (§8). Listo para implementar cuando se
autorice.

**Prerrequisito (Fase 4B, aún no hecho):** **instalar Ollama** y `ollama pull
qwen2.5`, y resolver el origen del texto de evidencia (ADR-017 §5). **No se ha
instalado nada todavía.**

**Riesgos / notas:**
- En CPU, un 7B genera pocos tokens/s: latencia a vigilar en la demo.
- La garantía **anti-alucinación** se diseña en 4B (prompt estricto + post-proceso
  que verifica que cada cita existe entre los chunks recuperados, RNF-05).

**Estado de Fase 4A (cerrada, diseño):** modelo LLM decidido (ADR-016, P-29);
trazabilidad RF-09/10/11 vinculada. Sin código y sin dependencias nuevas
instaladas.

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
