# 95 · Análisis técnico de los fallos del Retriever

> Análisis de **causa raíz** de las consultas con baja precisión o resultados no
> relevantes detectadas en la evaluación formal (`94_EVALUACION_RECUPERACION.md`).
> Distingue, **con datos del corpus**, qué fallos se deben a **ausencia real de
> evidencia** y cuáles a **limitaciones del modelo de embeddings** (MiniLM), y qué
> técnicas (híbrido, re-ranking) los resolverían. **Sin LLM, sin código** — solo
> análisis académico. Relacionado con ADR-012/014, P-22, P-32.

---

## 1. Objetivo

Para cada consulta problemática de la evaluación, determinar la **causa probable**
del fallo y clasificarla en una de dos familias —**ausencia/escasez de evidencia
en el corpus** vs **limitación del modelo/recuperación**— para fundamentar las
mejoras futuras de forma **empírica** y no especulativa.

## 2. Inventario de evidencia por fenómeno (medido sobre 27 280 eventos)

| Fenómeno | Señal en el log | Conteo real | ¿Existe evidencia? |
|---|---|---:|---|
| HTTP 404 | `status=404` | 7 080 | Sí, abundante |
| HTTP 503 | `status=503` | 218 | Sí, suficiente |
| Redirect 301 | `status=301` | 8 936 | Sí, abundante |
| CORS / preflight | `method=OPTIONS` | 4 556 (api-polla: 4 550) | **Sí, abundante** |
| Sin contenido 204 | `status=204` | 4 355 (todo api-polla) | **Sí, abundante** |
| Backend caído (outage) | `backend=…/<NOSRV>` con 5xx | 144 (vs 8 936 `<NOSRV>` de redirect) | Escasa (mezclada con redirects) |
| **Timeout** | `status=504` / term-state | **0** | **NO existe** |
| Health checks | rutas `/health`,`/status`,`/hc` | ~12–50 (dispersas) | Muy escasa |
| Errores app 5xx | `status>=500` | 218 (503) | Sí (≡ 503) |
| APIs | rutas `/api…` | 10 027 (api-polla: 9 893) | **Sí, abundante** |
| IIS (app específica) | app `…-iis-devl` | **2** eventos | **Casi inexistente** |
| Auth no autorizado | `status∈{401,403}` | 13 (401: 2, 403: 11) | **Casi inexistente** |
| POST | `method=POST` | 1 842 | Sí, pero difuso |

> Este inventario es la **base objetiva** del análisis: separa "el dato no está" de
> "el dato está pero no se recuperó".

## 3. Análisis por consulta problemática

> Resultados (top-1/top-3) tomados de `94_EVALUACION_RECUPERACION.md` §4.

### Q06 · Timeout — "timeout de conexion tiempo de espera agotado"
- **Resultados:** chunks `200/204` genéricos de api-polla (top-1 0.361).
- **¿Existe en el corpus?** **NO.** 0 eventos `504`; el esquema no captura
  `termination_state`, así que no hay señal de timeout.
- **¿Embeddings / vocabulario / frecuencia?** Ninguno: **no hay nada que
  recuperar**. El modelo devuelve lo más cercano (tráfico normal).
- **¿Híbrido? ¿Re-ranking?** **No ayudan** (no se puede recuperar evidencia
  inexistente). Solo **enriquecer el corpus**.
- **Causa raíz: AUSENCIA DE EVIDENCIA.**

### Q11 · Auth — "autenticacion fallida acceso no autorizado"
- **Resultados:** `200/204` genéricos; top-score **0.151** (el más bajo).
- **¿Existe?** **Casi no:** 13 eventos `401/403` en 27 280 (0,05 %). Imposible
  formar un chunk dominado por auth.
- **¿Frecuencia?** **Sí, decisiva:** la escasez impide cualquier recuperación útil.
- **¿Híbrido/Re-ranking?** Marginal (a lo sumo aflorarían 1–2 líneas sueltas; ningún
  chunk relevante). **Requiere corpus con auth real.**
- **Causa raíz: AUSENCIA/ESCASEZ DE EVIDENCIA.**

### Q07 · Health checks — "health check verificacion de estado del servicio"
- **Resultados:** `200/204` genéricos (top-1 0.266).
- **¿Existe?** **Muy escasa y dispersa** (~12 `/health`, ~50 `/status`); no hay
  chunk "de health" (la ventana de 20 eventos los diluye).
- **¿Vocabulario?** Secundario: aunque existieran más, "health check" en español no
  casa con rutas técnicas. **Frecuencia** es el factor dominante.
- **¿Híbrido/Re-ranking?** Parcial (BM25 sobre `/health` podría aflorar líneas),
  pero sin masa crítica el resultado seguiría siendo débil.
- **Causa raíz: ESCASEZ DE EVIDENCIA (+ vocabulario).**

### Q04 · CORS/204 — "peticiones OPTIONS preflight CORS sin contenido 204"
- **Resultados:** chunks `301`/GET de **api-account** (top-1 0.240). **Ningún**
  resultado con OPTIONS/204.
- **¿Existe?** **SÍ, abundante:** 4 550 `OPTIONS` y 4 355 `204` en **api-polla**.
- **¿Embeddings/vocabulario?** **SÍ, causa principal:** "CORS preflight" es
  terminología que **no aparece** en el log (que solo muestra `OPTIONS … 204`);
  MiniLM no conecta el concepto con la forma estructurada → **brecha semántica**.
- **¿Frecuencia?** No (la evidencia es masiva).
- **¿Híbrido?** **SÍ, lo resolvería** (BM25 sobre `OPTIONS`/`204` recupera los
  chunks correctos). **¿Re-ranking?** Solo si esos chunks entran antes en un top-N
  amplio; por sí solo **no** los rescata (no estaban en el pool top-3).
- **Causa raíz: LIMITACIÓN DEL MODELO (vocabulario/semántica).**

### Q09 · API — "peticiones a la API REST de notificaciones"
- **Resultados:** `301` de api-account con alguna ruta `/api/jsonws` (top-1 0.299).
- **¿Existe?** **SÍ, abundante:** 9 893 rutas `/api…` en api-polla (incl.
  `/api/notificaciones`), **no** recuperadas.
- **¿Vocabulario/embeddings?** **SÍ:** el modelo priorizó redirects `301` de
  api-account por similitud superficial en vez del tráfico real de API.
- **¿Híbrido?** **SÍ** (BM25 sobre `/api`). **¿Re-ranking?** Ayuda si se amplía el
  top-N.
- **Causa raíz: LIMITACIÓN DEL MODELO.**

### Q12 · POST — "metodo POST de creacion de recursos"
- **Resultados:** chunks `301`/GET con 1–2 POST; top-score **0.159**.
- **¿Existe?** Sí (1 842 POST) pero **difuso**: las líneas POST son
  estructuralmente casi idénticas a GET, sin un chunk "de POST".
- **¿Modelo/frecuencia?** Ambos: señal semántica débil + dispersión.
- **¿Híbrido?** **SÍ, parcial** (filtro/`method=POST` o BM25). **Re-ranking:**
  limitado.
- **Causa raíz: LIMITACIÓN DEL MODELO (+ dispersión).**

### Q05 · Backend caído — "backend sin servidor disponible NOSRV caido"
- **Resultados:** chunks `301` de `http_in/<NOSRV>` (top-1 0.325).
- **¿Existe?** Sí, pero **el outage real** (`<NOSRV>` con 5xx) son 144 eventos
  frente a 8 936 `<NOSRV>` que son **redirects** http→https (no caídas).
- **¿Modelo/intención?** El token `<NOSRV>` se recuperó **literalmente**, pero no la
  **intención** (caída): mezcla de **frecuencia** (redirect domina) y **constructo**.
- **¿Híbrido + filtro?** **SÍ:** filtrar por `severity=error` (ADR-014) aislaría los
  outages reales. **Re-ranking:** parcial.
- **Causa raíz: MODELO/FRECUENCIA (resoluble con filtro de severidad).**

### Q10 · IIS — "trafico al backend de windows iis"
- **Resultados:** tráfico `windows_*` genérico de api-polla (top-1 0.270).
- **¿Existe?** La app IIS específica tiene **2** eventos; "windows" es el backend de
  **casi todo** → consulta **ambigua/trivial**.
- **¿Frecuencia?** Sí: el fenómeno específico (IIS) es casi inexistente.
- **¿Híbrido/Re-ranking?** No ayudan a una consulta mal especificada; ayudaría
  **reformularla** o filtrar por `source_file`.
- **Causa raíz: ESCASEZ + AMBIGÜEDAD DE LA CONSULTA.**

## 4. Síntesis de causas

| Consulta | ¿Evidencia en corpus? | Causa primaria | ¿Híbrido ayuda? | ¿Re-ranking ayuda? |
|---|---|---|:---:|:---:|
| Q06 Timeout | No (0) | **Ausencia** | No | No |
| Q11 Auth | Casi no (13) | **Ausencia/escasez** | Marginal | No |
| Q07 Health | Muy escasa | **Escasez** | Parcial | No |
| Q10 IIS | Casi no (2) | **Escasez/ambigüedad** | No | No |
| Q04 CORS/204 | **Sí (≈4 500)** | **Modelo/vocabulario** | **Sí** | Parcial |
| Q09 API | **Sí (≈9 900)** | **Modelo/vocabulario** | **Sí** | Parcial |
| Q12 POST | Sí (1 842) | **Modelo/dispersión** | Sí (parcial) | Parcial |
| Q05 NOSRV | Sí, intención mezclada | **Modelo/frecuencia** | **Sí (filtro sev)** | Parcial |

## 5. Conclusiones cuantitativas

**Definición de "fallo":** consulta con top-1 **No relevante** (fallo duro) o
**parcial débil** (problemática).

- **Fallos duros (top-1 No relevante): Q04, Q06, Q07, Q11.**
  - Por **ausencia/escasez de evidencia**: Q06, Q07, Q11 → **75 %** (3/4).
  - Por **limitación del modelo MiniLM**: Q04 → **25 %** (1/4).

- **Conjunto problemático ampliado (8 consultas, incl. parciales débiles):**
  - **Ausencia/escasez (lado corpus):** Q06, Q07, Q10, Q11 → **50 %** (4/8).
  - **Limitación del modelo/recuperación (lado MiniLM):** Q04, Q05, Q09, Q12 →
    **50 %** (4/8).

> **Lectura clave:** **aproximadamente la mitad** de los problemas **no son
> corregibles con ninguna técnica de recuperación** —no hay datos que recuperar— y
> solo se resuelven **enriqueciendo el corpus**. La **otra mitad** sí es abordable,
> y de forma desproporcionada con **recuperación híbrida** (la evidencia existe pero
> falta la señal léxica). El **re-ranking por sí solo es insuficiente** en los peores
> casos (Q04/Q09): no puede promover documentos que **no entraron** al pool top-k.

## 6. Mejoras futuras recomendadas (priorizadas)

1. **Recuperación híbrida (BM25 léxico + densa).** Mayor ROI: resuelve Q04, Q09 y
   parcialmente Q12 (la evidencia existe; falta el match léxico de `OPTIONS`,
   `204`, `/api`, `POST`). Cierra P-22.
2. **Filtros de metadatos en la consulta** (`severity`, `status`, `method`,
   `source_file`) — ya soportados parcialmente por ADR-014 (`where`): resuelven Q05
   (`severity=error` para outages) y Q12 (`method=POST`).
3. **Re-ranking (cross-encoder)** sobre un **top-N ampliado** — complementa al
   híbrido reordenando candidatos; inútil si el relevante no está en el pool.
4. **Expansión/normalización de la consulta** — mapear lenguaje natural a señales
   del log: "no encontrado"→404, "caído"→503, "preflight/CORS"→OPTIONS/204.
5. **Enriquecer el corpus** — incluir `.gz` históricos y, si se consigue, logs con
   **timeout, health y auth reales**: única vía para Q06/Q07/Q11 (no son problema de
   técnica de recuperación).
6. **Modelo de embeddings más fuerte / específico** (e5, bge, o *fine-tuning* sobre
   logs) — sube el piso semántico de los casos del lado-modelo.

## 7. Valor académico

Este análisis convierte una métrica agregada (Precisión@k, doc 94) en un
**diagnóstico de causa raíz fundamentado en datos**: separa con rigor los fallos
**imputables al corpus** de los **imputables al modelo**, y **prioriza** las mejoras
en consecuencia. Es un aporte metodológico defendible —demuestra entender **por qué**
falla el sistema, no solo **que** falla— y **justifica empíricamente** la hoja de
ruta (híbrido > re-ranking; enriquecimiento de corpus para fenómenos ausentes) antes
de invertir en la Fase 4B.

---

> **Base de datos del análisis:** inventario de fenómenos medido con la librería del
> proyecto sobre el corpus real (27 280 eventos); resultados de recuperación de
> `94_EVALUACION_RECUPERACION.md`. Solo-lectura (ADR-005); sin LLM; sin cambios de
> código.
