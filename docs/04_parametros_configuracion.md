# 04 · Parámetros de configuración

> Catálogo **único y autoritativo** de todos los parámetros configurables del
> sistema. Regla del proyecto: **ningún valor mágico en el código**; todo
> parámetro vive aquí documentado.

Cada parámetro indica: **qué controla, valor por defecto (provisional), rango/
opciones, y efecto de cambiarlo** (incluido si obliga a reindexar).

> ⚠️ Los valores por defecto son **provisionales** hasta que se decidan vía ADR
> ([`05_bitacora_decisiones.md`](05_bitacora_decisiones.md)) en su fase. Esta
> tabla se llena conforme se implementa cada componente.

---

## 1. Convenciones

- **Ámbito:** dónde aplica el parámetro (Ingesta, Chunking, Embeddings, etc.).
- **Reindexa:** "Sí" si cambiarlo invalida el índice y obliga a reconstruirlo.
- **Sensibilidad:** impacto típico del cambio (Bajo / Medio / Alto).
- Los parámetros se externalizarán en un archivo de configuración (formato a
  decidir vía ADR; candidato: `.env` + `config.yaml`).

---

## 2. Ingesta

| Parámetro | Qué controla | Default (prov.) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `logs_path` | Carpeta/ruta de los logs de ejemplo | `./data/logs` | ruta válida | Sí | Alta |
| `file_pattern` | Patrón de archivos a ingerir | `*.log` | glob | Sí | Media |
| `encoding` | Codificación de lectura | `utf-8` | utf-8, latin-1… | Sí | Media |
| `source_type` | Forzar tipo de fuente o autodetectar | `auto` | auto/haproxy/iis | Sí | Media |

## 3. Parsing

| Parámetro | Qué controla | Default (Fase 1) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `haproxy_log_format` | Variante de log HAProxy a parsear | `http` | `http` (MVP) | Sí | Alta |
| `iis_fields_from_header` | Tomar las columnas del `#Fields:` del propio archivo IIS | `true` | true/false | Sí | Alta |
| `iis_fields` | Campos W3C por defecto si no hay cabecera `#Fields:` | _(lista W3C estándar, ver §3.1)_ | lista de campos | Sí | Alta |
| `on_parse_error` | Qué hacer con líneas no parseables | `skip` | skip/fail/keep | Sí | Media |

> **Definido en Fase 1.** El parser HAProxy implementa la variante **HTTP log**
> (la más común para diagnóstico web). El parser IIS lee las columnas de la
> directiva `#Fields:` presente en el propio archivo (`iis_fields_from_header=true`);
> `iis_fields` solo se usa como _fallback_ si el archivo no la incluye.

#### §3.1 Lista W3C por defecto (`iis_fields`)

```
date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username
c-ip cs(User-Agent) sc-status sc-substatus sc-win32-status time-taken
```

| Política `on_parse_error` | Comportamiento ante una línea no parseable |
|---|---|
| `skip` (default) | Se descarta y se incrementa un contador; el proceso continúa. |
| `keep` | Se incluye el evento con campos nulos pero conservando `raw`/`line_number`. |
| `fail` | Se aborta el parseo con error (útil para validar un formato nuevo). |

## 4. Normalización

| Parámetro | Qué controla | Default (prov.) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `timezone` | Zona horaria para normalizar timestamps | `UTC` | TZ válida | Sí | Media |
| `required_fields` | Campos obligatorios del evento | `timestamp,source` | lista | Sí | Media |

## 5. Chunking — **ADR-011** (decidido Fase 2A · **implementado Fase 2B**)

Configurado en `config.yaml` sección `chunking` (cargado por `src/config.py`).

| Parámetro | Qué controla | Default (ADR-011) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `chunk_strategy` | Cómo se agrupan los eventos | `by_events` | by_events (`by_time` previsto, no implementado) | Sí | Alta |
| `chunk_size` | Nº de eventos por chunk | `20` | entero > 0 | Sí | Alta |
| `chunk_overlap` | Solape entre chunks (eventos) | `4` | 0 ≤ x < chunk_size | Sí | Media |

> **Implementado (Fase 2B):** ventana de N eventos consecutivos con solape; cada
> chunk guarda metadatos de rango (archivo, líneas, timestamps, severidades) para
> citabilidad. `chunk_overlap` debe ser **menor** que `chunk_size` (validado al
> cargar). Override por CLI: `--chunk-size`, `--chunk-overlap`. Chunks grandes →
> más contexto, menor precisión.

## 6. Embeddings — **ADR-012** (decidido Fase 2A · **implementado Fase 2C**)

Configurado en `config.yaml` sección `embeddings` (cargado por `src/config.py`).

| Parámetro | Qué controla | Default (ADR-012) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `embedding_model` | Modelo que genera los vectores | `all-MiniLM-L6-v2` (local) | local/API | **Sí** | Alta |
| `embedding_dim` | Dimensión del vector (deriva del modelo, no se configura) | `384` | entero | **Sí** | Alta |
| `embedding_batch_size` | Nº de textos por lote al vectorizar | `32` | entero > 0 | No | Baja |

> **Implementado (Fase 2C):** embeddings **locales** (privacidad, coste cero,
> reproducibilidad) con `sentence-transformers`. `embedding_dim` **deriva** del
> modelo (no se configura). Cambiar `embedding_model` cambia la dimensión y
> **siempre** obliga a reindexar. Override por CLI: `--model`.

## 7. Vector store — **ADR-013** (decidido Fase 2A · **implementado Fase 2D**)

Configurado en `config.yaml` sección `vector_store` (cargado por `src/config.py`).

| Parámetro | Qué controla | Default (ADR-013) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `vector_backend` | Motor de la base vectorial | `chroma` (local, persistente) | chroma | Sí | Alta |
| `index_path` | Dónde se persiste el índice | `./data/index` | ruta | Sí | Media |
| `similarity_metric` | Métrica/espacio HNSW de la colección | `cosine` | cosine/l2/ip | Sí | Media |
| `collection_name` | Nombre de la colección Chroma | `tesisaiops` | texto | Sí | Media |

> **Implementado (Fase 2D):** **Chroma** local/persistente. Guarda vector +
> metadatos **aplanados** de citabilidad (`source_file`, `line_start/end`,
> `ts_*`, `sev_info/warning/error`, `embedding_dim`) — Chroma solo admite
> escalares. Indexa por **upsert** (idempotente: reindexar no duplica). El
> directorio `data/index/` está git-ignored. Cambiar la métrica o la dimensión
> del modelo obliga a **reconstruir** la colección.

## 8. Recuperación (Retriever) — **ADR-014** (decidido Fase 2A · **implementado Fase 3**)

| Parámetro | Qué controla | Default (ADR-014) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `top_k` | Nº de chunks recuperados por consulta | `5` | entero > 0 | No | Alta |
| `score_threshold` | Umbral mínimo de similitud | `0.0` (desactivado) | 0.0–1.0 | No | Media |
| `metadata_filters` | Pre-filtro por metadatos (tiempo, severidad, fuente, backend) | _(ninguno por defecto)_ | dict | No | Alta |

> **Decidido (ADR-014):** top-k denso (coseno) con **pre-filtrado opcional por
> metadatos**. ↑`top_k` → más recall, más ruido y más coste de prompt; filtros
> mal puestos pueden excluir evidencia. Híbrido/re-ranking quedan como mejora futura.

## 9. Orquestación RAG / Prompt

| Parámetro | Qué controla | Default (prov.) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `prompt_template` | Plantilla del prompt al LLM | _(por definir Fase 4)_ | texto | No | Alta |
| `max_context_tokens` | Presupuesto de tokens para el contexto | _(por decidir)_ | entero > 0 | No | Media |

## 10. Capa LLM

| Parámetro | Qué controla | Default (prov.) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `llm_model` | Modelo de lenguaje de respuesta | _(por decidir ADR)_ | API/local | No | Alta |
| `temperature` | Aleatoriedad de la generación | `0.1` | 0.0–1.0 | No | Media |
| `max_tokens` | Longitud máx. de la respuesta | `512` | entero > 0 | No | Media |

> Para un asistente de diagnóstico se prefiere **temperatura baja** (respuestas
> deterministas y fieles a la evidencia).

## 10.bis Salida del parser (Fase 1)

> Parámetros que controlan dónde y cómo el parser escribe los eventos normalizados.

| Parámetro | Qué controla | Default (Fase 1) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `processed_path` | Carpeta de salida de los eventos normalizados | `./data/processed` | ruta | No | Media |
| `parser_output_format` | Formato del archivo de eventos | `jsonl` | json/jsonl | No | Media |

> `jsonl` (un evento JSON por línea) es el default porque facilita el procesado
> incremental y el chunking de la Fase 2. `json` produce un único array (más
> cómodo de inspeccionar a ojo en archivos pequeños).

## 11. Interfaz / salida

| Parámetro | Qué controla | Default (prov.) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `output_format` | Formato de la respuesta | `text` | text/json | No | Baja |
| `show_citations` | Mostrar citas a líneas de log | `true` | true/false | No | Media |
| `verbose` | Nivel de detalle/diagnóstico | `false` | true/false | No | Baja |

## 12. Seguridad / operación

| Parámetro | Qué controla | Default (prov.) | Opciones/Rango | Reindexa | Sensibilidad |
|---|---|---|---|---|---|
| `read_only` | Garantiza solo lectura (sin acciones) | `true` (fijo) | true | No | Crítica |
| `api_key` | Credencial del proveedor LLM/embeddings | _(en `.env`)_ | secreto | No | Crítica |

> `read_only` es **invariante del MVP** (RNF-01): nunca se desactiva. Las
> credenciales **nunca** se versionan; van en `.env` (git-ignored).

---

## 13. Resumen: parámetros que obligan a reindexar

Cambiar cualquiera de estos invalida el índice y requiere re-ejecutar el pipeline
de indexación completo:

`logs_path`, `file_pattern`, `encoding`, `source_type`, `haproxy_log_format`,
`iis_fields_from_header`, `iis_fields`, `on_parse_error`, `timezone`,
`required_fields`, `chunk_*`, `embedding_model`, `embedding_dim`,
`vector_backend`, `index_path`, `similarity_metric`.

> Nota: `processed_path` y `parser_output_format` **no** obligan a reindexar el
> vector store (solo cambian dónde/cómo se guarda la salida intermedia del parser).

---

> Cada vez que se introduzca o cambie un parámetro, **actualizar esta tabla** y,
> si la elección fue no trivial, registrar la decisión en
> [`05_bitacora_decisiones.md`](05_bitacora_decisiones.md).
