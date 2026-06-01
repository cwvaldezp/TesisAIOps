# 06 · Manual técnico

> Guía de **instalación, configuración y operación** del MVP. En la Fase 0 (actual)
> aún no hay código ejecutable; este manual establece la estructura y se irá
> completando conforme se implementen las fases.

---

## 1. Requisitos previos (provisional)

> Se confirmarán al implementar la Fase 1.

- **Sistema operativo:** Windows / Linux / macOS.
- **Python:** 3.10+ (versión exacta por confirmar vía ADR).
- **Git** para control de versiones.
- **Acceso a modelo de embeddings y LLM:** local o por API (por decidir).
- Espacio en disco para el índice vectorial.

## 2. Estructura del repositorio

```
TesisAIOps/
├── README.md · requirements.txt · .gitignore
├── config/                     # config.yaml + .env.example (ADR-008)
├── data/
│   ├── logs/                   # ENTRADA: logs de ejemplo (HAProxy, IIS)
│   └── processed/              # SALIDA: eventos normalizados (regenerable)
├── src/
│   ├── config.py · schema.py · parse_logs.py
│   ├── chunker.py · chunk_logs.py     # Fase 2B (ADR-011), stdlib pura
│   ├── embedder.py · embed_chunks.py  # Fase 2C (ADR-012), sentence-transformers local
│   └── parsers/                # haproxy.py · iis.py · timeutils.py
├── examples/
│   └── demo_haproxy_parser.py  # demo log -> parse_line() -> evento -> JSON
├── tests/                      # test_schema/haproxy/iis/parse_logs + adr010_conformance
└── docs/
    ├── 00_vision_general.md … 07_reglas_desarrollo.md (alias → 99)
    ├── 98_PREGUNTAS_DEFENSA.md · 99_REGLAS_DESARROLLO.md
    └── diagrams/               # flujo_general · arquitectura_mvp · secuencia_consulta (.mmd)
```

> La estructura de **código** (`src/`, `tests/`, `examples/`, `data/`, `config/`)
> ya existe desde la Fase 1; este manual se actualiza con cada fase.

## 3. Instalación (se completará en Fase 1)

```bash
# 1) Clonar el repositorio
git clone <url-del-repo> TesisAIOps
cd TesisAIOps

# 2) Crear entorno virtual (ejemplo)
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 3) Instalar dependencias (Fase 1: PyYAML + pytest)
pip install -r requirements.txt
```

## 4. Configuración

- Los parámetros se definirán en un archivo de configuración + `.env` para
  secretos (decisión ADR-007).
- **No versionar** `.env` (debe estar en `.gitignore`).
- Catálogo completo de parámetros: [`04_parametros_configuracion.md`](04_parametros_configuracion.md).

Ejemplo de `.env` (plantilla futura):

```dotenv
# Credenciales (NUNCA versionar)
API_KEY=tu_clave_aqui

# Rutas
LOGS_PATH=./data/logs
INDEX_PATH=./data/index
```

## 5. Preparar datos de ejemplo (Fase 1)

1. Colocar logs de ejemplo HAProxy/IIS en `./data/logs/`.
2. Verificar `file_pattern` y `encoding` en la configuración.
3. **Nunca** usar logs de producción con datos sensibles sin anonimizar.

## 6. Operación

### 6.0 Parsear logs (Fase 1 / 1.2 — implementado)

```bash
# Parsea ./data/logs -> ./data/processed (formato por defecto: jsonl)
python -m src.parse_logs

# Forzar salida como array JSON, o forzar la fuente:
python -m src.parse_logs --format json
python -m src.parse_logs --source haproxy

# Demostración del flujo log -> parse_line() -> evento -> JSON (Fase 1.2):
python -m examples.demo_haproxy_parser

# Pruebas (incluye conformidad con ADR-010):
python -m pytest -q
```

Salida: un archivo por log en `data/processed/<nombre>.events.{jsonl|json}` con
eventos normalizados de 13 campos (contrato ADR-010). Es **solo lectura** sobre
los logs; no toca infraestructura (ADR-005).

### 6.0bis Chunking (Fase 2B — implementado, ADR-011)

```bash
# Agrupa los eventos en chunks: *.events.jsonl -> *.chunks.jsonl
python -m src.chunk_logs

# Overrides puntuales (p. ej. para ver varias ventanas en los logs de ejemplo):
python -m src.chunk_logs --chunk-size 5 --chunk-overlap 1
```

Salida: `data/processed/<nombre>.chunks.jsonl`. Cada chunk agrupa N eventos
consecutivos (con solape) y guarda metadatos de rango (`line_start/end`,
`ts_start/end`, `severities`, `event_lines`) + `text`. **Stdlib pura: sin
embeddings ni librerías de IA.** Parámetros en `config.yaml` (sección `chunking`).

### 6.0ter Embeddings (Fase 2C — implementado, ADR-012)

```bash
# Vectoriza el text de cada chunk: *.chunks.jsonl -> *.embeddings.jsonl
python -m src.embed_chunks

# Override del modelo:
python -m src.embed_chunks --model all-MiniLM-L6-v2
```

Salida: `data/processed/<nombre>.embeddings.jsonl` (cada línea = `embedding` de
384 floats + `embedding_model`/`embedding_dim` + metadatos de citabilidad del
chunk). Usa un modelo **local** (`sentence-transformers`); la **primera vez
descarga** el modelo (~80 MB) desde HuggingFace. **No indexa en Chroma ni hace
RAG** (fases posteriores). Parámetros en `config.yaml` (sección `embeddings`).

### 6.1 Indexar logs (Fase 2, comando provisional)

```bash
# python -m src.index   # construye el índice vectorial a partir de los logs
```

### 6.2 Consultar (Fase 5, comando provisional)

```bash
# python -m src.ask "¿Por qué hubo errores 503 entre las 14:00 y 14:10?"
```

> Estos comandos son **placeholders**; sus nombres definitivos se fijarán al
> implementar las fases correspondientes y se documentarán aquí.

## 7. Verificación por fase

| Fase | Cómo verificar |
|------|----------------|
| 0 — Docs | Revisar que existan todos los archivos de `docs/` y diagramas. |
| 1 — Parser | El parser convierte logs de ejemplo a eventos normalizados. |
| 2 — Index | Se genera un índice consultable sin errores. |
| 3 — Retriever | Una consulta devuelve chunks relevantes. |
| 4 — LLM | La respuesta cita líneas de log reales. |
| 5 — Interfaz | La CLI responde una consulta end-to-end. |

## 8. Solución de problemas (se ampliará con el código)

| Síntoma | Causa probable | Acción |
|---|---|---|
| "No se encuentran logs" | `logs_path`/`file_pattern` mal configurados | Revisar config |
| "Índice vacío" en consulta | No se ejecutó la indexación | Indexar primero |
| Respuesta sin citas | Recuperación vacía o prompt mal configurado | Revisar `top_k`/prompt |
| Error de credenciales | `.env` ausente o `api_key` inválida | Configurar `.env` |

## 9. Visualizar los diagramas Mermaid

Los archivos `.mmd` en `docs/diagrams/` se pueden ver con:
- **VS Code** + extensión "Markdown Preview Mermaid Support".
- Editor en línea: <https://mermaid.live>.
- Renderizado automático en GitHub/GitLab dentro de bloques ` ```mermaid `.

## 10. Mantenimiento de la documentación

- Cambiar un parámetro → actualizar [`04_parametros_configuracion.md`](04_parametros_configuracion.md).
- Tomar una decisión → registrar ADR en [`05_bitacora_decisiones.md`](05_bitacora_decisiones.md).
- Cambiar un flujo → actualizar [`03_flujos.md`](03_flujos.md) y su `.mmd`.
- Nuevo requisito → registrar en [`01_trazabilidad.md`](01_trazabilidad.md).

---

> Estado: **Fase 0**. Las secciones de instalación y operación se activarán al
> implementar el código en las fases siguientes.
