# 94 · Evaluación de la recuperación (Retriever) sobre corpus real

> Evaluación **formal y reproducible** de la calidad del Retriever (ADR-014) sobre
> el corpus real HAProxy, con **12 consultas operativas**, **juicio de relevancia
> manual** anclado en evidencia objetiva y **métricas de precisión**. Amplía la
> validación cualitativa de `93_VALIDACION_RETRIEVER.md`. **Sin LLM.** Pregunta de
> defensa: **P-32**.

---

## 1. Objetivo

Medir, de forma **objetiva y honesta**, qué tan bien el Retriever recupera
evidencia **relevante** para consultas operativas reales, e identificar **dónde
funciona y dónde no**, como base empírica para la Fase 4B (generación con LLM).

## 2. Metodología

- **Corpus / colección:** `tesisaiops_validacion` (1 706 chunks; 27 280 eventos
  reales; ver `91_VALIDACION_CORPUS.md`).
- **Modelo de embeddings:** `all-MiniLM-L6-v2` (384-d, local, ADR-012).
- **Métrica de similitud:** coseno; `score = 1 − distancia` (ADR-014). `top_k = 3`.
- **Consultas:** 12, en español, sobre fenómenos operativos (ver §3).
- **Juicio de relevancia (rúbrica):** para cada chunk recuperado se leyó el
  **histograma real de códigos de estado / método / ruta** de sus eventos y se
  etiquetó:
  - **Relevante (R):** el fenómeno buscado **domina** el chunk (≈≥50 % de eventos).
  - **Parcialmente relevante (P):** el fenómeno **aparece** pero es minoritario.
  - **No relevante (N):** el fenómeno **no aparece**.
- **Ponderación:** R = 1.0, P = 0.5, N = 0.0 (se reportan también métricas
  estrictas, solo-R).
- **Anotador:** único (el autor). Limitación reconocida (ver §8).

> El juicio se ancla en datos verificables (los códigos reales de las líneas del
> chunk), no en la impresión sobre el score: es **reproducible**.

## 3. Consultas evaluadas

| ID | Tema | Consulta |
|----|------|----------|
| Q01 | HTTP 404 | "errores 404 pagina no encontrada" |
| Q02 | HTTP 503 | "servicio no disponible error 503" |
| Q03 | Redirect 301 | "redireccion de http a https codigo 301" |
| Q04 | CORS / OPTIONS 204 | "peticiones OPTIONS preflight CORS sin contenido 204" |
| Q05 | Backend caído | "backend sin servidor disponible NOSRV caido" |
| Q06 | Timeout | "timeout de conexion tiempo de espera agotado" |
| Q07 | Health checks | "health check verificacion de estado del servicio" |
| Q08 | Errores de aplicación | "errores internos de la aplicacion 5xx" |
| Q09 | APIs | "peticiones a la API REST de notificaciones" |
| Q10 | IIS / HAProxy (backend) | "trafico al backend de windows iis" |
| Q11 | Auth | "autenticacion fallida acceso no autorizado" |
| Q12 | POST | "metodo POST de creacion de recursos" |

## 4. Resultados

### 4.1 Tabla maestra (top-1 + etiquetas top-3)

| ID | top score | Evidencia dominante del top-1 (códigos reales) | top-1 | top-3 |
|----|----------:|------------------------------------------------|:-----:|:-----:|
| Q01 | 0.295 | 301:15, **404:5** | P | P,R,R |
| Q02 | 0.397 | 204:8, 200:7, **503:5** | P | P,P,R |
| Q03 | 0.360 | **301:20** | **R** | R,R,R |
| Q04 | 0.240 | 301:20 (GET; sin OPTIONS/204) | N | N,N,N |
| Q05 | 0.325 | 301:20 (`http_in/<NOSRV>`) | P | P,P,P |
| Q06 | 0.361 | 200:11, 204:9 (sin timeout/504) | N | N,N,N |
| Q07 | 0.266 | 200:13, 204:7 (sin patrón de health) | N | N,N,N |
| Q08 | 0.278 | **503:19**, 200:1 | **R** | R,P,R |
| Q09 | 0.299 | 301:20 (rutas incluyen `/api/jsonws`) | P | P,N,N |
| Q10 | 0.270 | 200:12, 204:8 (backend `windows_*`) | P | P,P,P |
| Q11 | 0.151 | 200:12, 204:8 (sin 401/403) | N | N,N,N |
| Q12 | 0.159 | GET:19, **POST:1** | P | P,P,N |

### 4.2 Evidencia destacada (top-3, códigos reales del log)

**Q03 · Redirect 301 — el más nítido (R,R,R):**
```
#1 0.360 api-account L2114-2133  status[301:20]  meth[GET:20]
#2 0.351 api-account L11119-11138 status[301:20] meth[GET:19 POST:1]
#3 0.349 api-account L562-581     status[301:20] meth[GET:20]
```

**Q08 · Errores 5xx — recuperación de outages reales (R,P,R):**
```
#1 0.278 api-polla L209-228     status[503:19 200:1]    meth[OPTIONS:19 GET:1]
#2 0.274 api-polla L977-996     status[204:8 200:7 503:5]
#3 0.269 api-polla L10737-10756 status[503:13 204:6 200:1]
```

**Q04 · CORS/204 — fallo ilustrativo (N,N,N):** la evidencia 204/OPTIONS **existe**
en el corpus (4 355 `204`, 4 556 `OPTIONS`, en `api-polla`), pero el Retriever
priorizó chunks `301`/GET de `api-account`. Es un **fallo de precisión real**
(documentos relevantes no recuperados), no ausencia de datos.

**Q06 · Timeout / Q11 · Auth — ausencia en el corpus (N,N,N):** no hay `504`
(timeout) y solo **2** eventos `401` en 27 280; la recuperación trae tráfico
genérico. El fallo se debe al **corpus**, no solo al modelo.

## 5. Métricas

> Rúbrica: R = 1.0, P = 0.5, N = 0.0. n = 12 consultas.

| Métrica | Valor | Definición |
|---|---:|---|
| **Precisión@1 (estricta, solo R)** | **0.17** (2/12) | top-1 plenamente relevante |
| **Precisión@1 (R o P)** | **0.67** (8/12) | top-1 al menos parcialmente relevante |
| **Precisión@1 (ponderada)** | **0.42** | media de la etiqueta del top-1 (R=1,P=0.5) |
| **Precisión@3 (ponderada)** | **0.40** | media de (Σ etiquetas top-3)/3 |
| **Éxito@3 (≥1 resultado R o P)** | **0.67** (8/12) | la consulta recupera *algo* útil en top-3 |

**Desglose por tema (top-1):**
- **Plenamente relevante (R):** Q03 (301), Q08 (5xx).
- **Parcialmente relevante (P):** Q01 (404), Q02 (503), Q05 (NOSRV), Q09 (API),
  Q10 (backend windows), Q12 (POST).
- **No relevante (N):** Q04 (CORS/204), Q06 (timeout), Q07 (health), Q11 (auth).

## 6. Análisis de resultados

- **Funciona bien** con fenómenos **frecuentes y léxicamente distintivos** cuyo
  término aparece en el log o se asocia fuerte: **301** (8 936 eventos, chunks
  puros → R), **503/5xx** (cabecera `503` literal → R), **404** (7 080 → P/R).
- **Funciona mal** en tres situaciones, todas **explicables**:
  1. **Fenómeno ausente del corpus** (timeout, auth 401/403, health) → no hay qué
     recuperar; el Retriever devuelve tráfico genérico (Q06, Q07, Q11).
  2. **Concepto difuso o multi-palabra** (CORS/preflight, POST de creación) cuya
     señal semántica no domina el embedding del log (Q04, Q12).
  3. **Recuperación asimétrica** pregunta-español ↔ texto-log: empuja los scores a
     un rango bajo (0.15–0.40) y mezcla resultados (Q01/Q02 con 301 intercalado).
- **Hallazgo clave (Q04):** los documentos relevantes (204/OPTIONS) **existían** y
  **no** fueron recuperados → confirma que el cuello de botella es la **densidad
  semántica** del modelo general, no el dato. Es el argumento más fuerte a favor de
  **recuperación híbrida** (léxica + densa) en trabajo futuro (P-22).

## 7. Amenazas a la validez

- **Validez interna (juicio de relevancia):** etiquetado por **un solo anotador**;
  aunque anclado en códigos reales, hay subjetividad en el umbral R/P. Mitigación:
  rúbrica explícita y evidencia objetiva por chunk (reproducible).
- **Validez de constructo:** la "relevancia" se aproxima por **presencia del código
  de estado** objetivo; no captura matices de intención (p. ej. Q05 recupera
  `<NOSRV>` literal pero son **redirecciones**, no **outages** → etiquetado P con
  nota).
- **Validez externa:** un solo corpus (HAProxy de una institución, ventana de
  fechas acotada); resultados **no** generalizables a otros entornos sin reevaluar.
- **Validez estadística:** **n = 12** consultas; sin intervalos de confianza. Las
  métricas son **indicativas**, no concluyentes.
- **Sesgo de selección de consultas:** las consultas las definió el autor; podría
  favorecer fenómenos conocidos del corpus.

## 8. Limitaciones

1. **Anotador único** (sin acuerdo inter-evaluador, p. ej. κ de Cohen).
2. **Sin *gold set* exhaustivo** ni cálculo de **recall**: se mide precisión@k, no
   cobertura (¿se recuperó *toda* la evidencia relevante?).
3. **Scores absolutos bajos** por recuperación asimétrica; dificulta un
   `score_threshold` único.
4. **Cita a nivel de chunk** (≈20 eventos), no a la línea exacta.
5. **Corpus HAProxy-only**: fenómenos como timeout/health/auth están **ausentes o
   son escasísimos**, penalizando esas consultas por **falta de datos**.
6. **Modelo general** (MiniLM), no especializado en logs.

## 9. Trabajo futuro

- **Recuperación híbrida** (BM25 léxico + densa) y/o **re-ranking** con
  cross-encoder (cierra el fallo de Q04; ver P-22).
- ***Gold set*** anotado por ≥2 evaluadores y cálculo de **recall**, **MAP**,
  **nDCG** e **inter-anotador** (κ).
- **Normalización de la consulta** (expansión con códigos, p. ej. añadir "404"
  cuando se dice "no encontrado").
- **Corpus enriquecido** (incluir `.gz` históricos y, si se consigue, **W3C-IIS
  real**) para cubrir timeout/health/auth.
- **Cita a línea exacta** dentro del chunk.

## 10. Conclusiones

La evaluación formal muestra que el Retriever **recupera evidencia relevante de
forma fiable para los fenómenos bien representados y distintivos** del corpus
(redirects 301, errores 5xx, 404), con **Precisión@1 = 0.67** considerando
resultados al menos parcialmente relevantes (**0.42** ponderada) y **Éxito@3 =
0.67**. Las fallas son **pocas y explicables**: ausencia del fenómeno en el corpus
o conceptos semánticamente difusos, con un camino de mejora claro (**híbrido /
re-ranking**). El experimento es **honesto, reproducible y defendible**: documenta
tanto las capacidades como los límites del componente **antes** de construir la
capa LLM (Fase 4B) sobre él.

---

## 11. Valor académico

Esta evaluación aporta a la tesis una **medición objetiva** (no anecdótica) de un
componente de IA: define consultas, una **rúbrica de relevancia anclada en datos
reales**, **métricas estándar** (precisión@k) y un análisis crítico con **amenazas
a la validez**. Demostrar con rigor **dónde falla** el Retriever —y por qué— es tan
valioso como mostrar dónde acierta: evidencia la **madurez metodológica** del
trabajo y **justifica empíricamente** las decisiones siguientes (recuperación
híbrida futura; anclaje estricto de citas en Fase 4B, ADR-017).

---

> **Reproducción:** 12 consultas ejecutadas con la librería del proyecto
> (`src/retriever.py` + `src/embedder.py` + `src/vector_store.py`) sobre
> `tesisaiops_validacion`; relevancia juzgada contra el histograma de códigos
> reales de cada chunk. Solo-lectura (ADR-005); sin LLM; sin cambios de código.
