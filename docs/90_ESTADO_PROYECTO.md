# 90 · Estado del proyecto (fotografía)

> Instantánea del estado de TesisAIOps en una fecha concreta. Sirve para retomar
> el proyecto tras una pausa sabiendo **exactamente** dónde quedó. Se actualiza al
> cerrar cada fase/sub-fase.

---

## Resumen

| Campo | Valor |
|---|---|
| **Fecha de la foto** | 2026-06-01 |
| **Versión (paquete)** | `0.1.0` (`src/__init__.py`) · **hito: Fase 2B cerrada** |
| **Último commit** | `beb0eab` chore: add gitattributes · `0f3d331` feat: close phase 2b chunker pipeline |
| **Rama** | `main` (sincronizada con `origin/main`) |
| **Remoto** | https://github.com/cwvaldezp/TesisAIOps.git |
| **Estado global** | 🟢 Pipeline de **ingesta → parseo → normalización → chunking** funcional. Sin IA todavía. |
| **Próximo objetivo** | **Fase 2C — Embeddings (ADR-012)** |
| **Hito siguiente previsto** | **Fase 2C — Embeddings** (requiere aprobar `sentence-transformers`) |

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

**Flujos demostrables hoy:**
- `log (HAProxy/IIS) → parse_line() → evento normalizado (13 campos) → JSON`
- `*.events.jsonl → Chunker → *.chunks.jsonl`

## Fases pendientes

| Fase | Descripción | Requisito(s) | ADR | Prerrequisito |
|------|-------------|--------------|-----|---------------|
| **2C** | **Embedder** (vectorizar chunks) | RF-05 | ADR-012 | **Instalar `sentence-transformers`** (requiere aprobación) |
| 2D | Vector store (indexar) | RF-06 | ADR-013 | Instalar `chromadb` |
| 3 | Retriever (recuperación) | RF-08, RF-07 | ADR-014 | — |
| 4 | Capa LLM (respuesta con citas) | RF-09, RF-10, RF-11 | _(pendiente ADR)_ | Decidir modelo LLM |
| 5 | Interfaz de consulta + demo | RF-12, RF-07 | ADR-006 | — |

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
| 012 | Embeddings locales (MiniLM) | Aceptada (diseño) |
| 013 | Vector store Chroma | Aceptada (diseño) |
| 014 | Recuperación top-k + filtros | Aceptada (diseño) |

> Pendiente de decisión (sin ADR aún): **modelo LLM** (Fase 4).

## Preguntas de defensa (24)

`P-01 … P-24` en [`98_PREGUNTAS_DEFENSA.md`](98_PREGUNTAS_DEFENSA.md), en formato
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

## Métricas actuales

| Métrica | Valor |
|---|---|
| Pruebas (pytest) | **40 / 40 en verde** |
| Archivos de prueba | 7 (`tests/test_*.py`) |
| Módulos Python (`src/`) | 10 |
| Scripts de ejemplo | 1 (`examples/demo_haproxy_parser.py`) |
| Documentos (`docs/`) | 12 `.md` + 3 diagramas `.mmd` |
| ADRs | 14 |
| Preguntas de defensa | 24 |
| Requisitos funcionales cumplidos | RF-01, RF-02, RF-03, RF-04 (4 / 12) |
| Commits | 2 |
| Dependencias externas | PyYAML, pytest (sin librerías de IA todavía) |

**Cobertura de requisitos funcionales:**

| RF | Descripción | Estado |
|----|-------------|--------|
| RF-01 | Ingerir HAProxy | ✅ |
| RF-02 | Ingerir IIS | ✅ |
| RF-03 | Normalizar a esquema común | ✅ |
| RF-04 | Chunking | ✅ |
| RF-05 | Embeddings | 📋 (diseño ✅) |
| RF-06 | Indexar (vector store) | 📋 (diseño ✅) |
| RF-07 | Consulta en lenguaje natural | 📋 |
| RF-08 | Recuperar chunks | 📋 (diseño ✅) |
| RF-09 | Ensamblar contexto/prompt | 📋 |
| RF-10 | Generar respuesta (LLM) | 📋 |
| RF-11 | Citar líneas de log | 📋 |
| RF-12 | Interfaz de consulta | 📋 |

---

## Próximo objetivo: Fase 2C — Embeddings

**Qué:** implementar el **Embedder** (ADR-012): convertir el `text` de cada chunk
(`*.chunks.jsonl`) en un vector con un modelo **local** `all-MiniLM-L6-v2`
(384 dimensiones).

**Por qué ahora:** es el paso natural tras el chunking — el chunk es la unidad de
texto lista para vectorizar. Habilita después la indexación (2D) y la recuperación
(3), el corazón del RAG.

**Prerrequisito (bloqueante):** instalar `sentence-transformers`. Por las reglas
del proyecto, **requiere aprobación explícita** antes de añadir la dependencia; se
hará en su propio paso verificable, manteniendo el chunker como entrada estable.

**Riesgos / notas:**
- Cambiar el modelo de embeddings cambia la dimensión y **obliga a reindexar**.
- Embeddings locales por **privacidad** (los logs no salen del equipo, ADR-012).

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
