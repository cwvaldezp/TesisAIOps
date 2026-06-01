# 01 · Trazabilidad

> Matriz que conecta **objetivos → requisitos → componentes → decisiones →
> artefactos**. Permite, ante cualquier cambio o pregunta del jurado, rastrear
> "¿por qué existe esto?" y "¿qué se ve afectado si cambia?".

---

## 1. Cómo se usa este documento

- Cada **requisito** tiene un ID estable (`RF-xx` funcional, `RNF-xx` no funcional).
- Cada requisito se mapea a uno o más **objetivos específicos** (OE, ver
  [`00_vision_general.md`](00_vision_general.md)).
- Cada requisito se mapea a **componentes** (ver [`02_arquitectura.md`](02_arquitectura.md))
  y a **decisiones** (ADR en [`05_bitacora_decisiones.md`](05_bitacora_decisiones.md)).
- El **estado** se actualiza conforme avanzan las fases.

Estados posibles: `📋 Planificado` · `🛠️ En curso` · `✅ Hecho` · `⏸️ Diferido`.

## 2. Requisitos funcionales

| ID | Requisito | OE | Componente(s) | ADR | Fase | Estado |
|----|-----------|----|--------------|-----|------|--------|
| RF-01 | Ingerir archivos de log HAProxy de ejemplo | OE1 | Ingesta, Parser HAProxy | ADR-008 | 1 | ✅ |
| RF-02 | Ingerir archivos de log IIS (W3C) de ejemplo | OE1 | Ingesta, Parser IIS | ADR-008 | 1 | ✅ |
| RF-03 | Normalizar logs a un esquema común | OE1 | Normalizador | ADR-003, ADR-010 | 1 | ✅ |
| RF-04 | Trocear (chunking) los logs normalizados | OE2 | Chunker | ADR-011 | 2 | ✅ |
| RF-05 | Generar embeddings de cada chunk | OE2 | Embedder | ADR-012 | 2 | ✅ |
| RF-06 | Indexar embeddings en una base vectorial | OE2 | Vector store | ADR-013 | 2 | ✅ |
| RF-07 | Aceptar consultas en lenguaje natural | OE3 | Interfaz / API consulta | — | 5 | 📋 |
| RF-08 | Recuperar los chunks más relevantes a la consulta | OE3 | Retriever | ADR-014 | 3 | 📋 (diseño ✅) |
| RF-09 | Ensamblar contexto y construir el prompt | OE4 | Orquestador RAG | — | 3 | 📋 |
| RF-10 | Generar respuesta con un LLM | OE4 | Capa LLM | — | 4 | 📋 |
| RF-11 | Citar las líneas de log que sustentan la respuesta | OE4 | Capa LLM / Postproceso | — | 4 | 📋 |
| RF-12 | Exponer la consulta vía CLI o interfaz mínima | OE3 | Interfaz | — | 5 | 📋 |

## 3. Requisitos no funcionales

| ID | Requisito | Tipo | ADR | Estado |
|----|-----------|------|-----|--------|
| RNF-01 | No ejecutar acciones sobre infraestructura real (solo lectura) | Seguridad | ADR-005 | 🛠️ |
| RNF-02 | Parámetros externalizados y documentados | Mantenibilidad | ADR-007, ADR-008 | 🛠️ |
| RNF-03 | Cada decisión técnica registrada como ADR | Trazabilidad | ADR-009 | 🛠️ |
| RNF-04 | Cada flujo relevante con diagrama Mermaid | Documentación | — | ✅ |
| RNF-05 | Respuestas con citas verificables (sin alucinación) | Confiabilidad | ADR-010 | 📋 |
| RNF-06 | Reproducibilidad mediante manual técnico | Operabilidad | — | 🛠️ |
| RNF-07 | Código comentado explicando propósito | Mantenibilidad | — | 🛠️ |
| RNF-08 | MVP entendible y defendible (simplicidad sobre completitud) | Calidad | ADR-009 | 🛠️ |

## 4. Mapa Objetivo → Requisitos

| Objetivo específico | Requisitos asociados |
|---|---|
| OE1 — Parsear/normalizar | RF-01, RF-02, RF-03 |
| OE2 — Indexar (RAG) | RF-04, RF-05, RF-06 |
| OE3 — Recuperar | RF-07, RF-08, RF-12 |
| OE4 — Generar respuesta con citas | RF-09, RF-10, RF-11 |
| OE5 — Documentar y trazar | RNF-02, RNF-03, RNF-04, RNF-06, RNF-07, RNF-08 |

## 5. Mapa Requisito → Artefacto (se completará por fase)

> A medida que se implemente cada fase, se enlazará aquí el archivo de código,
> el test y el diagrama que satisface cada requisito.

| Requisito | Artefacto de código | Test | Diagrama |
|---|---|---|---|
| RF-01 | `src/parsers/haproxy.py` | `tests/test_haproxy_parser.py` | `diagrams/flujo_general.mmd` |
| RF-02 | `src/parsers/iis.py` | `tests/test_iis_parser.py`, `tests/test_adr010_conformance.py` | `diagrams/flujo_general.mmd` |
| RF-03 | `src/schema.py`, `src/parse_logs.py`, `src/parsers/haproxy.py`, `examples/demo_haproxy_parser.py` | `tests/test_schema.py`, `tests/test_parse_logs.py`, `tests/test_adr010_conformance.py` | `03_flujos.md` §2.1 / `02_arquitectura.md` §3.3.1 |
| RF-04 | `src/chunker.py`, `src/chunk_logs.py` | `tests/test_chunker.py`, `tests/test_chunk_logs.py` | `03_flujos.md` §2.2 |
| RF-05 | `src/embedder.py`, `src/embed_chunks.py` | `tests/test_embedder.py`, `tests/test_embed_chunks.py` | `03_flujos.md` §2.3 |
| RF-06 | `src/vector_store.py`, `src/index_embeddings.py` | `tests/test_vector_store.py`, `tests/test_index_embeddings.py` | `03_flujos.md` §2.4 |
| RF-08 | _(pendiente Fase 3)_ | _(pendiente)_ | `diagrams/secuencia_consulta.mmd` |
| … | … | … | … |

## 6. Verificación de R17 (cadena completa de cada decisión)

> **Regla R17:** toda decisión técnica se vincula con sus cinco anclas:
> **Objetivo específico · Requisito · Componente · ADR · Pregunta de defensa.**
> Esta tabla es el control de consistencia de extremo a extremo.

| ADR | Objetivo (OE) | Requisito | Componente | Pregunta(s) de defensa | Consistente |
|-----|---------------|-----------|------------|------------------------|-------------|
| ADR-001 | OE4 | RF-09..RF-11 | Orquestador RAG, Capa LLM | P-01 | ✅ |
| ADR-002 | OE2/OE3 | RF-04..RF-08 | Pipelines | P-02 | ✅ |
| ADR-003 | OE1 | RF-03 | Normalizador | P-03, P-18 | ✅ |
| ADR-004 | OE5 | RNF-03 | (proceso) | P-04 | ✅ |
| ADR-005 | OE5 | RNF-01 | (transversal) | P-05 | ✅ |
| ADR-006 | OE3 | RF-12 | Interfaz | P-06 | ✅ |
| ADR-007 | OE5 | RNF-02 | (config) | P-07 | ✅ |
| ADR-008 | OE5 | RNF-02 | `src/config.py` | P-07 | ✅ |
| ADR-009 | OE5 | RNF-03, RNF-08 | (proceso de revisión) | P-12 | ✅ |
| ADR-010 | OE1 | RF-03, RNF-05 | Normalizador (`src/schema.py`), Parsers HAProxy+IIS (`src/parsers/`) | P-13, P-14, P-15, P-16, P-17 | ✅ |
| ADR-011 | OE2 | RF-04 | Chunker (`src/chunker.py`, `src/chunk_logs.py`) | P-19, P-24 | ✅ |
| ADR-012 | OE2 | RF-05 | Embedder (`src/embedder.py`, `src/embed_chunks.py`) | P-20, P-25 | ✅ |
| ADR-013 | OE2 | RF-06 | Vector store (`src/vector_store.py`, `src/index_embeddings.py`) | P-21 (cierra P-11), P-26 | ✅ |
| ADR-014 | OE3 | RF-08 | Retriever _(diseño)_ | P-22 | ✅ |

> Estado de la verificación a 2026-06-01: **sin huérfanos** — cada ADR tiene OE,
> requisito, componente (o "proceso/transversal" cuando es metodológico) y al
> menos una pregunta de defensa. Las preguntas P-08..P-11 son de detalle técnico
> de Fase 1/2 y se enlazan a RF-03 (P-08/P-10) y a la decisión pendiente de
> vector store (P-11), sin requerir fila de ADR propia todavía.

## 7. Registro de cambios de trazabilidad

| Fecha | Cambio | Responsable |
|-------|--------|-------------|
| 2026-05-30 | Creación de la matriz inicial de requisitos | Carlos Valdez |
| 2026-05-30 | Fase 1: RF-01/02/03 ✅; ADR-008; parser implementado y probado (15 tests) | Carlos Valdez |
| 2026-06-01 | ADR-010 (esquema de evento) vinculado a RF-03/RNF-05; ADR-009 a RNF-03/RNF-08; añadida verificación R17 (§6) | Carlos Valdez |
| 2026-06-01 | Fase 1.2: parser HAProxy verificado conforme a ADR-010 (test de conformidad + demo); 21 pruebas en verde; P-16 | Carlos Valdez |
| 2026-06-01 | Fase 1.3: parser IIS verificado conforme a ADR-010 (7 tests de conformidad); 28 pruebas en verde; P-17. **Fase 1 CERRADA** | Carlos Valdez |
| 2026-06-01 | Fase 2A (diseño): ADR-011/012/013/014 (chunking/embeddings/Chroma/recuperación); RF-04/05/06/08 con ADR; P-18..P-22; P-11 cerrada. Sin código | Carlos Valdez |
| 2026-06-01 | Fase 2B: Chunker implementado (ADR-011, stdlib); RF-04 ✅; P-23/P-24; 40 pruebas en verde. Sin librerías de IA | Carlos Valdez |
| 2026-06-01 | Añadido `docs/90_ESTADO_PROYECTO.md` (fotografía de estado); `.gitattributes`; repo publicado en GitHub | Carlos Valdez |
| 2026-06-01 | Fase 2C: Embedder implementado (ADR-012, sentence-transformers local 384-d); RF-05 ✅; P-25; 48 pruebas en verde. Sin Chroma ni RAG | Carlos Valdez |
| 2026-06-01 | Fase 2D: Vector store Chroma implementado (ADR-013, local persistente, upsert idempotente); RF-06 ✅; P-26; 57 pruebas en verde. Sin consultas NL/RAG/LLM | Carlos Valdez |

---

> **Regla:** ningún requisito nuevo se implementa sin entrar primero en esta
> matriz y vincularse a un objetivo, un componente y (si aplica) una decisión.
