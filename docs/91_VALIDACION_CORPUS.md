# 91 · Validación con corpus real (Fase 3.5)

> Resultados de ejecutar el pipeline de indexación **completo** (parse →
> chunking → embeddings → índice Chroma) sobre **logs reales** del balanceador
> HAProxy de la USFQ. **Sin LLM**: se valida y se mide la ingesta y la
> construcción de evidencia, no la generación de respuestas. Decisión asociada:
> **ADR-015**. Pregunta de defensa: **P-28**.

---

## 1. Objetivo y alcance

Confirmar que el MVP, probado hasta Fase 3 con logs **sintéticos**, funciona con
**datos reales** y medir su comportamiento. Alcance de esta **primera corrida**
(acordado con el autor):

- **Subconjunto:** el archivo `.log` **vigente** de tres aplicaciones (no los
  `.gz` rotados todavía).
- **Fuente forzada:** `haproxy` (ver hallazgo §3).
- **Métricas:** nº de eventos, chunks, embeddings y **tiempo de indexación**.

Reproducible con:

```bash
python -m src.validate_corpus \
  data/logs/api-account-devl/api-account-devl.usfq.edu.ec.log \
  data/logs/api-polla-deployer-test/api-polla-deployer-test.usfq.edu.ec.log \
  data/logs/app-portal-sitios-iis-devl/app-portal-sitios-iis-devl.usfq.edu.ec.log
```

Reporte JSON crudo: `data/processed/corpus_validation.json`.

## 2. Entorno de la medición

| Parámetro | Valor |
|---|---|
| Fecha | 2026-06-02 |
| Modelo de embeddings | `all-MiniLM-L6-v2` (local, 384-d) |
| `chunk_size` / `chunk_overlap` | 20 / 4 (ADR-011) |
| Métrica / backend | coseno / Chroma persistente (ADR-013) |
| Colección | `tesisaiops_validacion` (separada del índice de demo) |
| `on_parse_error` | `skip` |

## 3. Hallazgos (lo que el corpus real reveló)

Los logs reales destaparon **tres desajustes** que los samples sintéticos
ocultaban (corregidos en **ADR-015**):

1. **Compresión y estructura.** El corpus son 269 archivos: un `.log` vigente por
   app + decenas de `.log-YYYYMMDD.gz` rotados, en **una subcarpeta por
   aplicación**. Se añadió lectura `.gz` transparente e ingesta recursiva
   (`src/ingest.py`).
2. **Cabeceras capturadas (crítico).** El formato real de HAProxy inserta uno o
   dos bloques `{...}` (p. ej. `{api-account-devl.usfq.edu.ec}`, el `Host`) entre
   las colas y la petición. El regex previo **no** los contemplaba → **el 100 %
   de las líneas reales caía como no parseable** (0 eventos). Se hizo el patrón
   tolerante a 0–2 bloques, **retrocompatible** con el sample.
3. **Nombre engañoso.** `app-portal-sitios-iis-devl` **no es IIS/W3C**: su
   contenido es HAProxy (el "iis" es el *backend* Windows). Tratarlo por el parser
   IIS habría dado 0 eventos. **El corpus es HAProxy-only**; la validación
   W3C-IIS real queda pendiente de un log W3C verdadero.

## 4. Resultados por aplicación

| Aplicación (`.log` vigente) | Líneas | Eventos | Chunks | Embeddings | t. parse | t. embed |
|---|---:|---:|---:|---:|---:|---:|
| api-account-devl | 16 088 | 16 073 | 1 005 | 1 005 | 0,096 s | 31,291 s |
| api-polla-deployer-test | 11 204 | 11 204 | 700 | 700 | 0,108 s | 17,328 s |
| app-portal-sitios-iis-devl | 3 | 3 | 1 | 1 | 0,001 s | 0,068 s |
| **TOTAL** | **27 295** | **27 280** | **1 706** | **1 706** | **0,205 s** | **48,687 s** |

> **Nota:** el `.log` vigente de `app-portal-sitios-iis-devl` casi no tiene datos
> (su historial vive en los `.gz`); por eso aporta 3 eventos. Es esperable dado el
> alcance "solo `.log` vigente" de esta corrida.

## 5. Métricas globales y tiempos

| Métrica | Valor |
|---|---|
| Archivos procesados | 3 |
| Líneas leídas | 27 295 |
| **Eventos** normalizados | **27 280** (99,95 % de las líneas) |
| Líneas no parseables (omitidas, `skip`) | 15 (0,05 %) |
| **Chunks** generados | **1 706** |
| **Embeddings** (384-d) | **1 706** |
| Puntos en el índice Chroma | 1 706 |
| Carga del modelo (1ª vez incluye descarga) | 9,897 s |
| Parseo | 0,205 s |
| Chunking | 0,060 s |
| Embeddings (CPU) | 48,687 s |
| **Indexación (Chroma upsert)** | **2,215 s** |

**Lectura de los números:**

- El **cuello de botella es el embedding en CPU** (~48,7 s para 1 706 chunks ≈
  **35 chunks/s**), no el parseo (27 k líneas en ~0,2 s) ni la indexación (2,2 s).
- El **parseo es prácticamente perfecto** (99,95 %); las 15 líneas omitidas son
  formatos no-HTTP residuales (arranques/TCP), descartados de forma segura.
- La razón **eventos→chunks** ≈ 16 (coherente con `step = 20 − 4`).
- La **indexación es barata y estable** gracias al `upsert` idempotente (ADR-013):
  reindexar no duplica.

## 6. Conclusiones

- El pipeline **funciona de extremo a extremo con datos reales** tras ADR-015.
- A esta escala (decenas de miles de líneas) **el sistema es holgado**: si se
  añadieran los `.gz` (todo el histórico de las 3 apps o las 11), el tiempo crece
  básicamente con el nº de chunks **a embeber**, no con el parseo ni el índice.
- **Sin LLM aún**: esta fase valida la **recuperación de evidencia**, no la
  generación.

## 7. Pendientes / próximos pasos (no en esta corrida)

- Incluir los `.gz` rotados (`file_patterns: ["*.log","*.gz"]`, `recursive: true`)
  para medir el corpus completo y estresar el embedding.
- Conseguir un **log W3C-IIS real** para validar de verdad el parser IIS.
- Corte por fecha del rotado y posible batch/aceleración del embedding.
- **Fase 4 (LLM):** pendiente de ADR de selección de modelo (no se aborda aquí).

---

> Generado a partir de `python -m src.validate_corpus` (arnés de medición,
> solo-lectura, ADR-005). Datos crudos en `data/processed/corpus_validation.json`.
