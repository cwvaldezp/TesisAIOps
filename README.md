# TesisAIOps

> Asistente inteligente basado en **NLP + RAG + LLM** para consultar logs de
> **HAProxy / IIS** y apoyar el diagnóstico de incidentes operativos.

Proyecto de tesis (MVP). El objetivo no es un producto comercial, sino una
**prueba de concepto entendible, demostrable y defendible** que muestre cómo
las técnicas de IA aplicada (recuperación aumentada por generación) ayudan a un
operador de infraestructura a investigar incidentes a partir de logs.

---

## 1. ¿Qué problema resuelve?

Cuando ocurre un incidente (latencia, errores 5xx, caídas de backend), el
operador suele revisar **manualmente** miles de líneas de log de HAProxy e IIS.
Esto es lento, propenso a error y depende del conocimiento tácito del experto.

TesisAIOps propone un asistente que:

1. **Ingiere** logs HAProxy/IIS (archivos planos, sin tocar infraestructura real).
2. Los **normaliza** y **trocea** (parsing + chunking).
3. Los **indexa** semánticamente (embeddings + base vectorial → RAG).
4. Permite **preguntar en lenguaje natural** (NLP) y responde con un LLM citando
   las líneas de log relevantes.

## 2. Alcance del MVP

| Sí incluye | No incluye (todavía) |
|---|---|
| Parsing de logs HAProxy/IIS de ejemplo | Conexión a infraestructura productiva |
| Indexación RAG sobre archivos locales | Agentes autónomos complejos |
| Consulta en lenguaje natural | Acciones correctivas automáticas |
| Respuestas con citas a líneas de log | Multi-tenant / autenticación robusta |
| Documentación y trazabilidad completas | Alta disponibilidad / escalado |

> **Restricción de seguridad:** el MVP **nunca** ejecuta acciones sobre
> infraestructura real. Solo lee archivos de log proporcionados.

## 3. Estructura del repositorio

```
TesisAIOps/
├── README.md                         # Este archivo: punto de entrada
└── docs/
    ├── 00_vision_general.md          # Problema, objetivos, alcance, glosario
    ├── 01_trazabilidad.md            # Requisitos ↔ decisiones ↔ artefactos
    ├── 02_arquitectura.md            # Componentes y responsabilidades
    ├── 03_flujos.md                  # Flujos de ingesta y consulta
    ├── 04_parametros_configuracion.md# Catálogo de parámetros configurables
    ├── 05_bitacora_decisiones.md     # Registro de decisiones técnicas (ADR)
    ├── 06_manual_tecnico.md          # Guía de instalación y operación
    ├── 07_reglas_desarrollo.md       # (alias → 99) redirección, no editar aquí
    ├── 90_ESTADO_PROYECTO.md         # Fotografía del estado (fases, ADRs, métricas)
    ├── 98_PREGUNTAS_DEFENSA.md       # Banco de preguntas para la defensa (tipo tribunal)
    ├── 99_REGLAS_DESARROLLO.md       # CANÓNICO: reglas R1–R18 + roles de revisión
    └── diagrams/
        ├── flujo_general.mmd         # Diagrama Mermaid: flujo end-to-end
        ├── arquitectura_mvp.mmd      # Diagrama Mermaid: arquitectura
        └── secuencia_consulta.mmd    # Diagrama Mermaid: secuencia de consulta
```

## 4. Cómo navegar la documentación

1. **Empieza por** [`docs/00_vision_general.md`](docs/00_vision_general.md) — el qué y el porqué.
2. Revisa la [`docs/02_arquitectura.md`](docs/02_arquitectura.md) — el cómo a alto nivel.
3. Profundiza en [`docs/03_flujos.md`](docs/03_flujos.md) — los flujos paso a paso.
4. Consulta parámetros en [`docs/04_parametros_configuracion.md`](docs/04_parametros_configuracion.md).
5. Sigue las decisiones en [`docs/05_bitacora_decisiones.md`](docs/05_bitacora_decisiones.md).
6. **Reglas obligatorias** del proyecto en [`docs/99_REGLAS_DESARROLLO.md`](docs/99_REGLAS_DESARROLLO.md) (R1–R18 + roles de revisión).
7. Prepárate para la defensa con [`docs/98_PREGUNTAS_DEFENSA.md`](docs/98_PREGUNTAS_DEFENSA.md).

## 5. Estado actual

🟢 **Fase 2D — Vector store Chroma implementado (ADR-013).**
El pipeline de **indexación** está completo: parseo → chunking → embeddings →
**indexación en Chroma** local y persistente (RF-06), con metadatos de
citabilidad y `upsert` idempotente. **Aún NO hay consulta en lenguaje natural,
RAG ni LLM** (fases posteriores). **57 pruebas en verde** (la lógica se prueba sin
cargar el modelo ni Chroma).

Ejecutar:

```bash
pip install -r requirements.txt
python -m src.parse_logs                  # logs -> eventos: ./data/processed/*.events.jsonl
python -m src.chunk_logs                  # eventos -> chunks: ./data/processed/*.chunks.jsonl
python -m src.embed_chunks                # chunks -> embeddings: ./data/processed/*.embeddings.jsonl
python -m src.index_embeddings            # embeddings -> Chroma: ./data/index/
python -m pytest -q                       # ejecuta las 57 pruebas
```

Flujos demostrables:
- `log (HAProxy/IIS) → parse_line() → evento normalizado → JSON` (Fase 1)
- `*.events.jsonl → Chunker → *.chunks.jsonl` (Fase 2B)
- `*.chunks.jsonl → Embedder → *.embeddings.jsonl` (embeddings + metadata) (Fase 2C)
- `*.embeddings.jsonl → Chroma (data/index/)` (índice citable y filtrable) (Fase 2D)

## 6. Reglas de trabajo del proyecto

> 📜 La gobernanza formal y ampliada (**R1–R18**, incluidos los 5 roles de
> revisión y la Definición de "Hecho") vive en
> [`docs/99_REGLAS_DESARROLLO.md`](docs/99_REGLAS_DESARROLLO.md), que es la
> **fuente canónica**. El siguiente resumen se mantiene por contexto rápido.

Este proyecto se desarrolla bajo reglas estrictas de calidad y trazabilidad:

1. Todo archivo de código se comenta explicando su propósito.
2. Todo parámetro configurable se documenta en `docs/04_parametros_configuracion.md`.
3. Toda decisión técnica se registra en `docs/05_bitacora_decisiones.md`.
4. Todo flujo importante tiene un diagrama Mermaid.
5. Cada módulo declara: qué hace, cuándo se invoca, entradas, salidas, fallos
   posibles y efecto de cambiar sus parámetros.
6. No se implementan funcionalidades grandes sin documentar antes el flujo.
7. Se trabaja en fases pequeñas y verificables.
8. No se ejecutan acciones sobre infraestructura real.
9. No se crean agentes complejos todavía.
10. Se prioriza un MVP entendible, demostrable y defendible.

**Revisión por roles (R13–R14).** Ningún cambio está "Hecho" hasta pasar **cinco
revisiones**, cada una desde un rol: 🏛️ Arquitecto · 🐍 Desarrollador Python ·
📝 Documentador · 🔗 Revisor de Trazabilidad · 🎓 Tutor de Defensa. Son roles
**metodológicos** del proceso de desarrollo (checklists), **no** agentes de
software (la regla 9 sigue vigente para el producto). Detalle en
[`docs/99_REGLAS_DESARROLLO.md`](docs/99_REGLAS_DESARROLLO.md).

## 7. Roadmap por fases

- [x] **Fase 0** — Estructura + documentación base.
- [x] **Fase 1** — Parser de logs HAProxy/IIS sobre archivos de ejemplo (actual).
- [ ] **Fase 2** — Chunking + embeddings + indexación vectorial.
- [ ] **Fase 3** — Recuperación (retriever) + ensamblado de contexto.
- [ ] **Fase 4** — Capa LLM de respuesta con citas.
- [ ] **Fase 5** — Interfaz de consulta (CLI o web mínima) + demo.

---

**Autor:** Carlos Valdez · **Tipo:** Tesis (MVP) · **Última actualización:** 2026-05-30
