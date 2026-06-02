# 05 · Bitácora de decisiones (ADR)

> Registro cronológico de **decisiones técnicas** (Architecture Decision Records).
> Regla del proyecto: **toda decisión técnica se registra aquí** con su contexto,
> alternativas y consecuencias. Esto hace el proyecto **defendible**: ante el
> jurado, cada elección tiene su justificación rastreable.

---

## Cómo se registra una decisión

Cada ADR usa esta plantilla:

```
### ADR-XXX · Título corto
- Fecha:
- Estado: Propuesta | Aceptada | Rechazada | Sustituida por ADR-YYY
- Contexto: por qué se necesita decidir.
- Decisión: qué se decidió.
- Alternativas consideradas: opciones y por qué se descartaron.
- Consecuencias: efectos positivos y negativos / compromisos.
- Requisitos/Parámetros afectados: enlaces a RF/RNF y a parámetros.
```

Estados: `Propuesta` → `Aceptada`/`Rechazada`. Una decisión puede ser
`Sustituida` más tarde (no se borra: se marca y se enlaza a la nueva).

---

## Índice de decisiones

| ADR | Título | Estado | Fecha |
|-----|--------|--------|-------|
| ADR-001 | Adoptar arquitectura RAG (no LLM puro) | Aceptada | 2026-05-30 |
| ADR-002 | Separar pipelines de indexación y consulta | Aceptada | 2026-05-30 |
| ADR-003 | Normalizar HAProxy e IIS a un esquema común | Aceptada | 2026-05-30 |
| ADR-004 | Documentación primero, código después (doc-driven) | Aceptada | 2026-05-30 |
| ADR-005 | MVP solo-lectura, sin acciones sobre infraestructura | Aceptada | 2026-05-30 |
| ADR-006 | Empezar por CLI antes que interfaz web | Aceptada | 2026-05-30 |
| ADR-007 | Externalizar todos los parámetros | Aceptada | 2026-05-30 |
| ADR-008 | Formato de configuración: YAML + `.env` | Aceptada | 2026-05-30 |
| ADR-009 | Metodología de revisión multi-rol + Definition of Done | Aceptada | 2026-05-30 |
| ADR-010 | Esquema de campos del evento normalizado (13 campos) | Aceptada | 2026-05-30 |
| ADR-011 | Estrategia de chunking (ventana de eventos con solape) | Aceptada (diseño) | 2026-06-01 |
| ADR-012 | Embeddings locales (sentence-transformers MiniLM) | Aceptada (diseño) | 2026-06-01 |
| ADR-013 | Vector store local: Chroma (persistente) | Aceptada (diseño) | 2026-06-01 |
| ADR-014 | Estrategia de recuperación (top-k denso + filtros de metadatos) | Aceptada · **implementado (Fase 3)** | 2026-06-01 |
| ADR-015 | Soporte de corpus real: lectura `.gz`, cabeceras capturadas HAProxy, ingesta recursiva | Aceptada · **implementado (Fase 3.5)** | 2026-06-02 |

---

### ADR-001 · Adoptar arquitectura RAG (no LLM puro)
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** El asistente debe responder sobre **logs concretos** que el LLM
  no conoce. Un LLM solo, sin acceso a los datos, alucinaría.
- **Decisión:** Usar **RAG** (Retrieval-Augmented Generation): recuperar primero
  los fragmentos de log relevantes y entregarlos al LLM como contexto.
- **Alternativas consideradas:**
  - *LLM puro con prompt:* descartado, no conoce los logs y alucina.
  - *Fine-tuning sobre logs:* descartado para el MVP (costoso, poco flexible,
    requiere reentrenar por cada conjunto de logs).
- **Consecuencias:** (+) respuestas ancladas en evidencia y auditables; (+)
  flexible ante nuevos logs sin reentrenar. (−) añade componentes (embeddings,
  vector store, retriever) y un paso de indexación.
- **Afecta a:** RF-08, RF-09, RF-10, RF-11; toda la arquitectura.

---

### ADR-002 · Separar pipelines de indexación y consulta
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** Indexar es costoso y por lotes; consultar es ligero e interactivo.
- **Decisión:** Diseñar **dos pipelines desacoplados** que comparten el vector store.
- **Alternativas consideradas:**
  - *Indexar en cada consulta:* descartado, lento y caro de repetir.
- **Consecuencias:** (+) se puede reindexar sin afectar la consulta; (+) claridad
  conceptual y de demostración. (−) hay que gestionar la coherencia del índice.
- **Afecta a:** arquitectura, flujos de indexación y consulta.

---

### ADR-003 · Normalizar HAProxy e IIS a un esquema común
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** HAProxy (HTTP log) e IIS (W3C) tienen formatos distintos.
- **Decisión:** Mapear ambos a un **evento normalizado** común. Los campos
  concretos de ese esquema se definen en **ADR-010** (no incluye un campo
  "mensaje": `raw` conserva el texto íntegro).
- **Alternativas consideradas:**
  - *Tratar cada fuente por separado en todo el pipeline:* descartado, duplica
    lógica aguas abajo.
- **Consecuencias:** (+) el resto del sistema es agnóstico a la fuente; (+)
  fácil añadir nuevas fuentes. (−) requiere mantener mapeos por fuente.
- **Afecta a:** RF-03; componente Normalizador.

---

### ADR-004 · Documentación primero, código después
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** Es un proyecto de tesis que debe ser **defendible y trazable**.
- **Decisión:** Adoptar enfoque **doc-driven**: documentar visión, arquitectura,
  flujos, parámetros y decisiones **antes** de implementar cada funcionalidad.
- **Alternativas consideradas:**
  - *Codificar primero y documentar al final:* descartado, pierde trazabilidad y
    dificulta la defensa.
- **Consecuencias:** (+) trazabilidad total; (+) cada cambio tiene contexto. (−)
  más disciplina y tiempo inicial antes de ver código.
- **Afecta a:** RNF-03, RNF-04, RNF-07; metodología del proyecto.

---

### ADR-005 · MVP solo-lectura, sin acciones sobre infraestructura
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** El sistema analiza incidentes, pero actuar sobre producción es
  riesgoso y fuera del alcance de un MVP de tesis.
- **Decisión:** El MVP **solo lee** archivos de log; **nunca** ejecuta acciones
  correctivas ni se conecta a infraestructura real. `read_only` es invariante.
- **Alternativas consideradas:**
  - *Permitir acciones sugeridas/automáticas:* diferido a trabajo futuro.
- **Consecuencias:** (+) seguridad y alcance acotado; (+) defendible sin riesgo.
  (−) el asistente sugiere, no ejecuta.
- **Afecta a:** RNF-01; parámetro `read_only`.

---

### ADR-006 · Empezar por CLI antes que interfaz web
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** Se necesita una vía de consulta demostrable con mínimo esfuerzo.
- **Decisión:** Implementar primero una **CLI**; la interfaz web es opcional y
  posterior.
- **Alternativas consideradas:**
  - *Web desde el inicio:* descartado, añade complejidad sin valor para el MVP.
- **Consecuencias:** (+) demo rápida y enfocada en la lógica RAG. (−) menos
  vistosa para presentación (mitigable con una web mínima al final).
- **Afecta a:** RF-12; componente Interfaz.

---

### ADR-007 · Externalizar todos los parámetros
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** Reproducibilidad y experimentación (chunking, top_k, modelos…).
- **Decisión:** Ningún valor mágico en código; todos los parámetros se
  externalizan y se documentan en [`04_parametros_configuracion.md`](04_parametros_configuracion.md).
  Credenciales en `.env` (git-ignored).
- **Alternativas consideradas:**
  - *Hardcodear valores:* descartado, no reproducible ni mantenible.
- **Consecuencias:** (+) reproducibilidad y ajuste fino sencillo. (−) hay que
  mantener el catálogo de parámetros sincronizado.
- **Afecta a:** RNF-02; todo el catálogo de parámetros.

---

### ADR-008 · Formato de configuración: YAML + `.env`
- **Fecha:** 2026-05-30
- **Estado:** Aceptada (concreta y sustituye la fila pendiente de ADR-007)
- **Contexto:** ADR-007 decidió externalizar todos los parámetros, pero no fijó
  el **formato** concreto. En la Fase 1 ya se necesita configurar el parser
  (rutas, codificación, política ante errores, formato de salida), así que hay
  que concretar cómo se declara y se carga la configuración.
- **Decisión:** Usar **dos mecanismos complementarios**:
  1. **`config/config.yaml`** — parámetros **no sensibles** y versionables
     (rutas, `file_pattern`, `encoding`, `source_type`, `on_parse_error`,
     `parser_output_format`, `timezone`…). Se carga con **PyYAML**.
  2. **`.env`** — **secretos** (API keys de embeddings/LLM en fases futuras).
     **No se versiona** (incluido en `.gitignore`). En la Fase 1 aún no hay
     secretos; se deja `config/.env.example` como plantilla.
- **Alternativas consideradas:**
  - *Solo `.env`:* descartado, mal soporta estructura anidada y listas.
  - *JSON de configuración:* descartado, no admite comentarios (peor para
    documentar parámetros en el propio archivo).
  - *TOML:* válido, pero YAML es más conocido en el ecosistema de IA/MLOps y
    más legible para el jurado; se prioriza familiaridad.
  - *`.ini`/ConfigParser:* descartado, jerarquía y tipos limitados.
- **Consecuencias:** (+) configuración legible, comentable y jerárquica; (+)
  separación clara entre parámetros versionables y secretos; (+) un único punto
  de carga (`src/config.py`). (−) añade dependencia **PyYAML**; (−) hay que
  validar/normalizar tipos al cargar (rutas, enums).
- **Afecta a:** RNF-02; ADR-007 (lo concreta); todos los parámetros de
  [`04_parametros_configuracion.md`](04_parametros_configuracion.md); módulo
  `src/config.py`.

---

### ADR-009 · Metodología de revisión multi-rol + Definition of Done
- **Fecha:** 2026-05-30
- **Estado:** Aceptada
- **Contexto:** El proyecto necesita un mecanismo de calidad que garantice que
  cada cambio cumple las reglas (R1–R12) de forma sistemática y que sea
  **defendible** ante un tribunal. Hasta ahora las revisiones eran implícitas.
- **Decisión:** Adoptar **cinco roles de revisión** (Arquitecto, Desarrollador
  Python, Documentador, Revisor de Trazabilidad, Tutor de Defensa) y una
  **Definición de "Hecho"**: ningún cambio está completo hasta pasar las cinco
  revisiones. Se formaliza en [`99_REGLAS_DESARROLLO.md`](99_REGLAS_DESARROLLO.md)
  (reglas R13–R18). Además se amplían: preguntas tipo tribunal (7 preguntas),
  vínculo obligatorio de cada decisión (OE↔RF↔componente↔ADR↔pregunta de defensa)
  y un formato de entrega de 8 apartados.
- **Aclaración clave:** estos "agentes" son **roles metodológicos de revisión**,
  NO agentes de software autónomos. No se conectan a infraestructura ni ejecutan
  acciones. La restricción "no crear agentes complejos todavía" (alcance del
  *producto*) y ADR-005 (solo-lectura) **siguen vigentes**: R13 aplica al
  *proceso de desarrollo*, no al sistema entregado.
- **Alternativas consideradas:**
  - *Revisión informal/ad-hoc:* descartada, no es trazable ni repetible.
  - *Una única checklist plana sin roles:* válida pero menos pedagógica; los
    roles obligan a mirar el cambio desde cinco perspectivas distintas.
  - *Implementar agentes de software de revisión reales:* descartado por
    complejidad y por contradecir el alcance del MVP (ver aclaración).
- **Consecuencias:** (+) calidad sistemática y defendible; (+) cinco perspectivas
  reducen puntos ciegos; (+) trazabilidad reforzada. (−) más trabajo por cambio;
  (−) riesgo de burocracia si se aplica a cambios triviales (mitigación: escalar
  el rigor al tamaño/relevancia del cambio, Regla 10).
- **Cómo se evalúa:** un cambio "pasa" si el cierre (formato de 8 apartados)
  evidencia las cinco revisiones y el banco de defensa queda actualizado.
- **Limitaciones:** al ser desempeñado por una sola persona/asistente, las cinco
  revisiones no son independientes entre sí (no hay separación real de
  responsables); es un control de calidad, no una auditoría externa.
- **Afecta a:** RNF-03, RNF-08; metodología global; documentos `99`, `98`, `01`.
- **Vínculo de trazabilidad (R17):** OE5 · RNF-03/RNF-08 · (proceso, sin
  componente de código) · ADR-009 · pregunta de defensa **P-12**.

---

### ADR-010 · Esquema de campos del evento normalizado (13 campos)
- **Fecha:** 2026-05-30
- **Estado:** Aceptada (concreta a ADR-003, que decidió "tener" un esquema común;
  este ADR define **cuáles son sus campos**).
- **Contexto:** ADR-003 decidió reducir HAProxy e IIS a un esquema común, pero no
  fijó su contrato de campos. El parser de la Fase 1 ya emite un evento de **13
  campos** (`src/schema.py`); falta formalizarlo, declarar qué es obligatorio vs
  opcional y definir cómo se extenderá a fuentes futuras. También hay que
  reconciliar una divergencia: `02_arquitectura.md` §3.3 mencionaba un campo
  "mensaje" que **no** existe en el esquema real (R8).
- **Decisión:** Adoptar como **contrato canónico** el evento de 13 campos, con
  **claves siempre presentes** y orden estable (apto para JSON/JSONL diff-eable):

  | Campo | Tipo | Obligatoriedad | Significado |
  |-------|------|----------------|-------------|
  | `source` | str (enum) | **Obligatorio, no nulo** | Fuente: `haproxy`\|`iis` (extensible). |
  | `severity` | str (enum) | **Obligatorio, no nulo** | `info`\|`warning`\|`error`, derivada del status. |
  | `source_file` | str | **Obligatorio, no nulo** | Archivo de origen (cita). |
  | `line_number` | int | **Obligatorio, no nulo** | Nº de línea de origen (cita). |
  | `raw` | str | **Obligatorio, no nulo** | Línea original íntegra (evidencia). |
  | `timestamp` | str ISO-8601 \| null | **Presente; nulo solo si no parseable** | Fecha/hora del evento. |
  | `client_ip` | str \| null | Opcional | IP del cliente. |
  | `method` | str \| null | Opcional | Método HTTP. |
  | `path` | str \| null | Opcional | Ruta (con query si aplica). |
  | `status_code` | int \| null | Opcional | Código de estado HTTP. |
  | `bytes` | int \| null | Opcional | Bytes de respuesta. |
  | `duration_ms` | int \| null | Opcional | Latencia/tiempo de servicio (ms). |
  | `backend` | str \| null | Opcional (solo HAProxy) | Backend/servidor. |

  **Principios del contrato:**
  1. **Esquema fijo, valores nullable:** todas las claves existen siempre; la
     ausencia de dato se representa con `null`, nunca omitiendo la clave.
  2. **5 campos núcleo no nulos** (`source`, `severity`, `source_file`,
     `line_number`, `raw`) garantizan identidad, clasificación y **citabilidad**.
  3. **Severidad derivada** del `status_code` (5xx=error, 4xx=warning, resto=info),
     no leída de la fuente, para coherencia entre orígenes.
  4. **No se añade un campo `message`** ahora: `raw` ya conserva el texto íntegro
     (Regla 10, evitar redundancia). Se reconcilia `02_arquitectura.md`.
- **Mapeo por fuente:** ver tablas en `03_flujos.md` §2.1 y `02_arquitectura.md`
  §3.3.1 (HAProxy: accept-date, backend/server, Tt; IIS: date+time, c-ip,
  cs-uri-stem+query, time-taken).
- **Eventos futuros (extensibilidad):**
  - Se añade un valor al **enum `source`** (p. ej. `syslog`, `app`, `healthcheck`).
  - Los campos HTTP-específicos (`method`, `path`, `status_code`, `backend`)
    quedan en `null` para fuentes no-HTTP; se apoyan en `severity` + `raw`.
  - `source_file`/`line_number`/`raw` se mantienen **siempre** (citabilidad).
  - Para datos estructurados propios de una fuente se introducirá, **cuando
    aparezca la primera fuente que lo requiera**, un campo opcional `attributes`
    (objeto clave→valor) mediante un **nuevo ADR** (YAGNI: no se crea aún).
- **Alternativas consideradas:**
  - *Esquema por fuente (sin unificar):* descartado (ADR-003).
  - *Añadir `message` + `attributes` ahora:* descartado por YAGNI/Regla 10; `raw`
    cubre el texto y no hay aún fuente que necesite `attributes`.
  - *Omitir claves nulas en el JSON:* descartado; un esquema fijo simplifica el
    consumo aguas abajo (chunking, indexación) y los diffs.
- **Consecuencias:** (+) contrato estable y predecible; (+) citabilidad asegurada;
  (+) extensible sin romper consumidores. (−) algo de redundancia (`raw` siempre);
  (−) sesgo HTTP actual: eventos no-HTTP dependen de `raw` hasta tener `attributes`.
- **Qué pasa si se cambia un campo:** añadir/renombrar un campo **rompe** el
  formato de salida y obliga a actualizar parsers, tests y a **reindexar** en
  fases futuras; por eso cualquier cambio de esquema exige nuevo ADR.
- **Cómo se evalúa:** `tests/test_schema.py` valida orden de claves y severidad;
  `tests/test_parse_logs.py` valida la presencia de los campos núcleo en la salida.
- **Limitaciones:** el esquema modela hoy **logs de acceso HTTP**; no representa
  aún métricas ni trazas; la temporalidad asume que el log ya está en `timezone`.
- **Afecta a:** RF-03; RNF-05 (citabilidad); componente Normalizador; `src/schema.py`.
- **Vínculo de trazabilidad (R17):** OE1 · RF-03/RNF-05 · Normalizador (`src/schema.py`)
  · ADR-003→ADR-010 · preguntas de defensa **P-13, P-14, P-15**.

---

> **Nota de fase (Fase 2A — solo diseño).** Los ADR-011 a ADR-014 son decisiones
> **de diseño**: se justifican y se aprueban ahora, pero **no** se implementan ni
> se instalan librerías todavía. Habilitan la planificación de la Fase 2 sin
> comprometer código. Dependencia natural entre ellos:
> **ADR-011 (chunking) → ADR-012 (embeddings) → ADR-013 (vector store) → ADR-014 (recuperación)**.

### ADR-011 · Estrategia de chunking (ventana de eventos con solape)
- **Fecha:** 2026-06-01 · **Estado:** Aceptada (diseño)
- **Contexto:** Antes de indexar hay que decidir **qué unidad de texto** se
  vectoriza. Los datos de entrada son **eventos normalizados** (ADR-010), no
  prosa: cada evento es corto y estructurado, y los incidentes se entienden mejor
  **en contexto temporal** (una ráfaga de 503 consecutivos, no un 503 aislado).
- **Decisión:** Chunking por **ventana de N eventos consecutivos con solape**
  (`chunk_strategy = by_events`). Cada chunk es la **serialización textual
  compacta** de N eventos (orden cronológico) más metadatos del rango
  (archivo, línea inicial/final, timestamp inicial/final, fuentes incluidas).
  Valores de partida (a afinar empíricamente): **N = 20 eventos, solape = 4**
  (20 %). Restricción: `0 ≤ solape < N`.
- **Justificación técnica:**
  - Un evento por chunk daría máxima precisión de cita pero **perdería la
    correlación** entre eventos vecinos (clave para diagnosticar incidentes).
  - Una ventana con solape **preserva el contexto local** y evita cortar una
    ráfaga justo en el borde del chunk.
  - Tamaño de chunk **predecible** → entradas homogéneas para el embedder y
    control del coste/longitud (a diferencia de chunking por tiempo, que produce
    chunks muy desiguales ante ráfagas).
  - Se conservan metadatos de rango para **mantener la citabilidad** (RNF-05).
- **Alternativas consideradas:** un evento = un chunk; ventana **temporal** fija
  (p. ej. 1 min); chunking por tamaño de tokens; chunking semántico.
- **Por qué no se eligieron:** evento único pierde contexto; ventana temporal da
  chunks desiguales (ráfagas); por-tokens es innecesario con eventos cortos;
  semántico añade complejidad sin beneficio claro para logs (Regla 10).
- **Qué pasa si se cambia un parámetro:** ↑N → menos chunks, más contexto, menor
  precisión de recuperación y mayor coste por chunk; ↑solape → más redundancia y
  más vectores. Cambiar la estrategia **obliga a reindexar**.
- **Cómo se evalúa:** inspección manual de chunks sobre los logs de ejemplo +
  medición de recall en un set pequeño de consultas de incidente (Fase 2/2B).
- **Limitaciones:** la ventana por conteo ignora "huecos" temporales largos entre
  eventos; podría mezclar dos periodos distantes en un mismo chunk (mitigable con
  un corte por salto temporal en el futuro).
- **Afecta a:** RF-04; parámetros `chunk_*`. **Vínculo R17:** OE2 · RF-04 ·
  Chunker · ADR-011 · P-19.

### ADR-012 · Embeddings locales (sentence-transformers MiniLM)
- **Fecha:** 2026-06-01 · **Estado:** Aceptada (diseño)
- **Contexto:** Cada chunk debe convertirse en un vector. La elección define
  **privacidad, coste, dimensión y dependencia externa**.
- **Decisión:** Usar **embeddings locales** con el modelo
  **`all-MiniLM-L6-v2`** (sentence-transformers), **384 dimensiones**, métrica
  coseno. Sin llamadas a APIs externas.
- **Justificación técnica:**
  - **Privacidad (decisiva):** los logs operativos pueden contener IPs, rutas y
    datos sensibles; con embeddings locales **ningún dato sale del equipo**,
    coherente con el espíritu de ADR-005 (no exponer infraestructura).
  - **Coste cero y sin API key:** no hay dependencia de un proveedor ni gasto por
    token; mejora la reproducibilidad de la tesis (cualquiera puede ejecutarla).
  - **Tamaño/rapidez:** MiniLM es pequeño y rápido en CPU; suficiente para
    recuperación semántica de un corpus pequeño de logs.
  - **Defendibilidad:** es un modelo ampliamente usado y citado como baseline.
- **Alternativas consideradas:** embeddings por API (OpenAI `text-embedding-3-small`,
  Cohere); modelos locales mayores (e5-large, bge-large); `fastembed` (ONNX).
- **Por qué no se eligieron:** las APIs implican **enviar logs a terceros**
  (privacidad) y coste/dependencia; los modelos grandes exigen más RAM/tiempo sin
  beneficio claro a esta escala; `fastembed` queda como **alternativa ligera**
  válida si se quiere evitar PyTorch (se podrá reconsiderar sin cambiar el diseño).
- **Qué pasa si se cambia un parámetro:** cambiar de modelo **cambia la dimensión**
  y **obliga a reindexar** todo el vector store; la métrica debe ser coherente con
  el modelo (coseno para MiniLM).
- **Cómo se evalúa:** relevancia de la recuperación sobre consultas de ejemplo
  (juicio cualitativo en el MVP; no hay benchmark formal de embeddings).
- **Limitaciones:** MiniLM está entrenado en lenguaje general, no en logs; podría
  no capturar matices muy técnicos; mitigable con la normalización (ADR-010), que
  ya da estructura y vocabulario consistente.
- **Afecta a:** RF-05; parámetros `embedding_*`. **Vínculo R17:** OE2 · RF-05 ·
  Embedder · ADR-012 · P-20.

### ADR-013 · Vector store local: Chroma (persistente)
- **Fecha:** 2026-06-01 · **Estado:** Aceptada (diseño). Resuelve la pregunta
  abierta **P-11**.
- **Contexto:** Hay que almacenar los vectores + metadatos y buscar por
  similitud. El corpus del MVP es **pequeño** (miles de chunks), local y de un
  solo usuario.
- **Decisión:** Usar **Chroma** como vector store **local y persistente**
  (en `./data/index`), guardando junto a cada vector sus **metadatos de
  citabilidad** (`source_file`, `line_number`, rango temporal, `severity`,
  `source`). Métrica coseno (coherente con ADR-012).
- **Justificación técnica:**
  - **Citabilidad de primera clase:** Chroma almacena documento + metadatos +
    embedding juntos y los **devuelve en la consulta**; esto es justo lo que el
    RAG necesita para citar la evidencia (RNF-05) **sin** mantener un mapa
    separado id→metadato.
  - **Simplicidad (Regla 10):** API sencilla, persistencia en disco integrada y
    **filtrado por metadatos** incorporado (útil para ADR-014).
  - **Local y embebido:** sin servidor que desplegar; coherente con un MVP
    reproducible y con la restricción de no añadir infraestructura.
- **Alternativas consideradas:** **FAISS**, Qdrant, Elasticsearch, PostgreSQL+pgvector.
- **Por qué no se eligieron:**
  - *FAISS:* excelente para ANN a gran escala, pero es **solo índice de vectores**;
    obligaría a gestionar los metadatos/citas en una estructura aparte → más
    código de pegamento sin necesidad a esta escala. Es la opción a reconsiderar
    **si el volumen crece** mucho.
  - *Qdrant/Elasticsearch:* requieren **servidor** (infraestructura adicional).
  - *pgvector:* exige PostgreSQL operativo; excesivo para el MVP.
- **Qué pasa si se cambia un parámetro:** cambiar de backend o de métrica, o
  cambiar el modelo de embeddings (dimensión), **obliga a reconstruir el índice**.
- **Cómo se evalúa:** correctitud del top-k devuelto y latencia sobre el corpus
  local de ejemplo.
- **Limitaciones:** Chroma no está pensado para escala masiva ni alta
  concurrencia; para producción a gran volumen se migraría a FAISS/Qdrant.
- **Afecta a:** RF-06; parámetros `vector_backend`, `index_path`,
  `similarity_metric`. **Vínculo R17:** OE2 · RF-06 · Vector store · ADR-013 ·
  P-21 (y cierra P-11).

### ADR-014 · Estrategia de recuperación (top-k denso + filtros de metadatos)
- **Fecha:** 2026-06-01 · **Estado:** Aceptada · **implementado (Fase 3, 2026-06-01)**
- **Contexto:** Dada una pregunta, hay que recuperar los chunks relevantes que se
  pasarán al LLM. Las consultas de operación suelen estar **acotadas** ("503
  entre las 14:00 y 14:10", "errores del backend be_api").
- **Decisión:** **Recuperación densa top-k** por similitud coseno sobre los
  embeddings, con **pre-filtrado opcional por metadatos** (rango temporal,
  `severity`, `source`, `backend`) y umbral de score opcional. Valores de
  partida: `top_k = 5`, `score_threshold = 0.0` (desactivado), métrica coseno.
- **Justificación técnica:**
  - El **filtrado por metadatos** aprovecha la estructura del esquema (ADR-010) y
    de los chunks (ADR-011) para acotar la búsqueda como hace un operador,
    mejorando la precisión en consultas con tiempo/severidad explícitos.
  - **top-k denso** es el núcleo estándar de RAG, simple y suficiente para el MVP.
  - Chroma (ADR-013) ya ofrece similitud + filtros, así que esta estrategia
    **no añade dependencias** (Regla 10).
- **Alternativas consideradas:** recuperación **híbrida** (BM25 léxico + densa);
  **MMR** (diversidad); **re-ranking** con cross-encoder.
- **Por qué no se eligieron:** híbrido y re-ranking aportan calidad pero **suben
  la complejidad** y el coste; MMR es útil si hay redundancia, aún no demostrada.
  Se dejan como mejoras evaluables tras medir el baseline (evitar complejidad
  prematura).
- **Qué pasa si se cambia un parámetro:** ↑`top_k` → más contexto (más recall,
  más ruido y más tokens al LLM); ↑`score_threshold` → menos chunks pero riesgo
  de quedarse sin contexto; los filtros mal puestos pueden **excluir** evidencia.
- **Cómo se evalúa:** precisión@k sobre un conjunto pequeño de consultas de
  incidente con respuesta conocida (Fase 2B/3).
- **Limitaciones:** la recuperación puramente densa puede fallar con términos
  exactos raros (IDs, códigos) donde lo léxico ayudaría; de ahí que el híbrido
  quede señalado como mejora futura.
- **Afecta a:** RF-07, RF-08; parámetros `top_k`, `score_threshold`, `similarity_metric`.
  **Vínculo R17:** OE3 · RF-07/RF-08 · Retriever · ADR-014 · P-22, P-27.
- **Implementación (Fase 3, 2026-06-01):** lógica pura y testeable en
  `src/retriever.py` (`distance_to_score`, `build_where`, `build_results`,
  `retrieve`) + CLI `src/retrieve.py` (`python -m src.retrieve "<consulta>"`,
  flags `--top-k/--source/--severity/--json`). `embed_fn` (Embedder, ADR-012) y
  `store` (Chroma, ADR-013) se **inyectan**, de modo que las pruebas
  (`tests/test_retriever.py`) corren **sin modelo ni chromadb**. Parámetros
  `top_k`/`score_threshold` externalizados (sección `retrieval` de `config.yaml`).
  **Solo recuperación de evidencia: sin prompt, sin LLM** (eso es Fase 4).
  **66 pruebas en verde.**

### ADR-015 · Soporte de corpus real: lectura `.gz`, cabeceras capturadas HAProxy e ingesta recursiva
- **Fecha:** 2026-06-02 · **Estado:** Aceptada · **implementado (Fase 3.5, 2026-06-02)**
- **Contexto:** Hasta la Fase 3 el pipeline se probó con **logs sintéticos**. Al
  incorporar el **corpus real** (logs del balanceador HAProxy de la USFQ, 269
  archivos) aparecieron tres desajustes que impedían procesarlo:
  1. Los logs reales se distribuyen **comprimidos** (`.log` vigente + decenas de
     `.log-YYYYMMDD.gz` rotados) y en **una subcarpeta por aplicación**.
  2. El formato real de HAProxy incluye **cabeceras capturadas** (`capture request
     header`, típicamente el `Host`): uno o dos bloques `{...}` entre las colas y
     la petición. El regex del sample sintético **no** los contemplaba → **el
     100 % de las líneas reales caía como no parseable** (0 eventos con `skip`).
  3. La **autodetección por nombre** clasificaba como IIS cualquier archivo cuyo
     nombre contuviera "iis" (p. ej. `app-portal-sitios-iis-devl`), aunque su
     **contenido es HAProxy** (el "iis" es el *backend* Windows, no el formato).
- **Decisión:**
  1. **Lectura transparente de `.gz`** con `gzip` (stdlib) según la extensión,
     sin descomprimir a disco; bytes no decodificables se reemplazan
     (`errors='replace'`) para no abortar por una línea con basura. Nuevo módulo
     `src/ingest.py` (`read_log_lines`, `discover_log_files`).
  2. **Ingesta recursiva y multi-patrón** opcional (`recursive`, `file_patterns`)
     para recorrer las subcarpetas por aplicación y elegir extensiones.
  3. **Regex HAProxy tolerante** a 0, 1 o 2 bloques `{...}` de cabeceras
     capturadas — **retrocompatible** con líneas sin captura.
  4. Para esta validación, **tratar todo el corpus como HAProxy** (`--source
     haproxy`): es lo que realmente es. La validación W3C-IIS verdadera se
     pospone hasta disponer de un log W3C real (no existe en el corpus actual).
  5. Nuevo arnés `src/validate_corpus.py` que mide el pipeline de extremo a
     extremo (**sin LLM**): eventos, chunks, embeddings y **tiempo de indexación**.
- **Justificación técnica:** sin descompresión y sin tolerar cabeceras
  capturadas, el corpus real daría **cero evidencia**; el resto del MVP (chunking,
  embeddings, índice, recuperación) ya estaba listo y solo dependía de poder
  **ingerir el formato real**. Mantener la corrección **retrocompatible** evita
  romper los tests/sample de Fase 1. Sin librerías nuevas (gzip es stdlib).
- **Alternativas consideradas:** (a) descomprimir los `.gz` a disco en un paso
  previo; (b) reescribir el parser con una gramática completa de HAProxy; (c)
  forzar el archivo "iis" por el parser IIS.
- **Por qué no se eligieron:** (a) duplica datos en disco y añade un paso manual;
  (b) excesivo para el MVP (Regla 10) cuando basta extender el patrón; (c)
  produciría 0 eventos porque su contenido es HAProxy, no W3C.
- **Qué pasa si se cambia un parámetro:** `file_patterns`/`recursive` cambian qué
  archivos entran (volumen → tiempo de indexación); incluir `*.gz` multiplica el
  corpus. La corrección del regex no altera los campos extraídos.
- **Cómo se evalúa:** `tests/test_ingest.py` (lectura `.gz`/plano, descubrimiento
  recursivo) y casos reales en `tests/test_haproxy_parser.py` (cabeceras
  capturadas, 1 y 2 bloques). Medición end-to-end en `docs/91_VALIDACION_CORPUS.md`.
- **Limitaciones:** la severidad/citabilidad no cambian; el corpus actual es
  **HAProxy-only** (sin W3C-IIS real); el filtrado por fecha del rotado `.gz`
  queda como mejora futura. NO se rompe el invariante de solo-lectura (ADR-005).
- **Afecta a:** RF-01/RF-02 (ingesta); parámetros `file_patterns`, `recursive`.
  **Vínculo R17:** OE1 · RF-01 · Ingesta (`src/ingest.py`, `src/parse_logs.py`) ·
  ADR-015 · P-28.

---

## Decisiones pendientes (a resolver en su fase)

| Tema | Fase | Notas |
|------|------|-------|
| Proveedor / modelo LLM | 4 | Calidad vs coste vs privacidad (¿local vs API?) |

---

> Al tomar una de estas decisiones, **mover la fila a un ADR numerado** arriba y
> actualizar la trazabilidad y los parámetros afectados.
