# 98 · Banco de Preguntas de Defensa

> Preparación para la **defensa de la tesis** (Regla 12). Cada decisión técnica
> relevante se traduce aquí en una pregunta probable del jurado, con respuesta
> corta, técnica, alternativas evaluadas y su relación con la tesis.

**Formato de cada entrada (preguntas tipo tribunal, Regla R16):** cada decisión
debe poder responder estas siete preguntas del tribunal:
1. ¿Por qué se eligió esta tecnología/enfoque?
2. ¿Qué problema resuelve?
3. ¿Qué alternativas existían?
4. ¿Por qué no se eligieron?
5. ¿Qué pasa si se cambia este parámetro?
6. ¿Cómo se evalúa / verifica?
7. ¿Qué limitaciones tiene?

> Las entradas se redactan con: `Respuesta corta · Respuesta técnica ·
> Alternativas · Por qué no · Qué pasa si cambia un parámetro · Cómo se evalúa ·
> Limitaciones · Relación con la tesis`. Las entradas P-01…P-10 (creadas antes de
> R16) se irán **enriqueciendo** con los apartados 5–7 a medida que se toquen;
> las nuevas ya nacen con el formato completo.

Cada pregunta enlaza con su ADR de origen en
[`05_bitacora_decisiones.md`](05_bitacora_decisiones.md) y, por R17, con su
objetivo, requisito y componente para trazabilidad de punta a punta.

---

## Índice

| # | Pregunta | Origen | Estado |
|---|----------|--------|--------|
| P-01 | ¿Por qué RAG y no un LLM puro? | ADR-001 | Decidido |
| P-02 | ¿Por qué separar indexación y consulta? | ADR-002 | Decidido |
| P-03 | ¿Por qué normalizar HAProxy e IIS a un esquema común? | ADR-003 | Decidido |
| P-04 | ¿Por qué documentar antes de programar? | ADR-004 | Decidido |
| P-05 | ¿Por qué el MVP es solo-lectura? | ADR-005 | Decidido |
| P-06 | ¿Por qué empezar por una CLI? | ADR-006 | Decidido |
| P-07 | ¿Por qué YAML + `.env` para la configuración? | ADR-008 | Decidido |
| P-08 | ¿Por qué cada evento conserva `raw`, `source_file` y `line_number`? | Fase 1 | Decidido |
| P-09 | ¿Por qué el parser usa solo la librería estándar de Python? | Regla 10 | Decidido |
| P-10 | ¿Por qué la severidad se deriva del código de estado HTTP? | Fase 1 | Decidido |
| P-11 | ¿Qué base vectorial se usará (FAISS, Chroma…)? | Fase 2 | Decidido (ADR-013 → ver P-21) |
| P-12 | ¿Por qué una metodología de revisión multi-rol ("agentes")? | ADR-009 | Decidido |
| P-13 | ¿Por qué se diseñó un esquema normalizado de eventos? | ADR-010 | Decidido |
| P-14 | ¿Por qué unos campos son obligatorios y otros opcionales? | ADR-010 | Decidido |
| P-15 | ¿Cómo soporta el esquema nuevas fuentes de eventos en el futuro? | ADR-010 | Decidido |
| P-16 | ¿Cómo se garantiza que el parser cumple el contrato ADR-010? | Fase 1.2 | Decidido |
| P-17 | ¿Por qué el evento IIS tiene campos en `null` sin romper el esquema? | Fase 1.3 | Decidido |
| P-18 | ¿Por qué se normalizaron los eventos antes que las técnicas de IA? | Fase 1/2A | Decidido |
| P-19 | ¿Por qué esta estrategia de chunking (ventana de eventos)? | ADR-011 | Decidido (diseño) |
| P-20 | ¿Por qué embeddings locales y este modelo (MiniLM)? | ADR-012 | Decidido (diseño) |
| P-21 | ¿Por qué Chroma como vector store y no FAISS? | ADR-013 | Decidido (diseño) |
| P-22 | ¿Por qué esta estrategia de recuperación (top-k + filtros)? | ADR-014 | Decidido |
| P-23 | ¿Por qué Chroma y no FAISS? (comparativa) | ADR-013 | Decidido (diseño) |
| P-24 | ¿Por qué el chunker agrupa por archivo y conserva metadatos de rango? | ADR-011 / Fase 2B | Decidido |
| P-25 | ¿Cómo se prueba el Embedder sin depender del modelo real? | ADR-012 / Fase 2C | Decidido |
| P-26 | ¿Cómo se guardan los metadatos en Chroma y por qué upsert? | ADR-013 / Fase 2D | Decidido |
| P-27 | ¿Cómo se convierte una consulta textual en evidencia recuperada sin usar todavía un LLM? | ADR-014 / Fase 3 | Decidido |
| P-28 | ¿Cómo se validó el pipeline con logs reales y qué desajustes revelaron frente a los sintéticos? | ADR-015 / Fase 3.5 | Decidido |

---

## P-01

### Pregunta
¿Por qué se utilizó una arquitectura RAG y no un LLM puro con prompt?

### Respuesta corta
Porque el asistente debe responder sobre **logs concretos** que el modelo no
conoce; sin recuperación, un LLM alucinaría.

### Respuesta técnica
RAG (Retrieval-Augmented Generation) recupera primero los fragmentos de log
relevantes y los entrega al LLM como contexto. Así las respuestas quedan
**ancladas en evidencia real** y son **auditables** (se puede mostrar la línea de
log exacta). Esto es clave para un asistente de diagnóstico de incidentes.

### Alternativas consideradas
- LLM puro con todo el log en el prompt.
- Fine-tuning del modelo sobre los logs.

### Por qué no se eligieron
- *LLM puro:* no conoce los logs y la ventana de contexto no escala a millones
  de líneas; tiende a inventar.
- *Fine-tuning:* costoso, rígido y exigiría reentrenar por cada conjunto de logs.

### Relación con la tesis
Permite recuperar incidentes, causas y resoluciones similares para apoyar el
diagnóstico, que es el objetivo central del MVP.

---

## P-02

### Pregunta
¿Por qué separar el pipeline de indexación del de consulta?

### Respuesta corta
Porque indexar es costoso y por lotes, mientras consultar es ligero e interactivo.

### Respuesta técnica
Desacoplar ambos pipelines (compartiendo el vector store) permite reindexar sin
afectar la consulta y mantiene cada parte simple y observable, facilitando la
demostración paso a paso.

### Alternativas consideradas
- Indexar en cada consulta (pipeline único).

### Por qué no se eligieron
Reindexar en cada pregunta es lento y desperdicia cómputo repitiendo trabajo.

### Relación con la tesis
Refleja una arquitectura realista de sistemas RAG y facilita explicar el flujo
en la defensa.

---

## P-03

### Pregunta
¿Por qué normalizar HAProxy e IIS a un mismo esquema de evento?

### Respuesta corta
Para que el resto del sistema sea **agnóstico a la fuente** del log.

### Respuesta técnica
HAProxy (HTTP log) e IIS (W3C) tienen formatos distintos. Mapearlos a un evento
común (timestamp, source, severity, status_code, path…) evita duplicar lógica
aguas abajo (chunking, indexación, recuperación) y permite añadir nuevas fuentes
con solo escribir un parser.

### Alternativas consideradas
- Procesar cada fuente por separado durante todo el pipeline.

### Por qué no se eligieron
Duplicaría la lógica de chunking/indexación/recuperación y complicaría el
mantenimiento.

### Relación con la tesis
Demuestra un diseño extensible y limpio, defendible como buena práctica de
ingeniería.

---

## P-04

### Pregunta
¿Por qué se documenta antes de programar (enfoque doc-driven)?

### Respuesta corta
Porque la tesis debe ser **trazable y defendible**, no solo funcional.

### Respuesta técnica
Documentar visión, arquitectura, flujos, parámetros y decisiones antes de
implementar garantiza que cada línea de código tenga un porqué rastreable
(requisito → componente → decisión → artefacto).

### Alternativas consideradas
- Codificar primero y documentar al final.

### Por qué no se eligieron
Documentar al final pierde el contexto de las decisiones y dificulta la defensa.

### Relación con la tesis
La trazabilidad es un criterio de evaluación explícito del proyecto.

---

## P-05

### Pregunta
¿Por qué el MVP es de solo lectura y no ejecuta acciones correctivas?

### Respuesta corta
Por seguridad y por acotar el alcance: el asistente **sugiere**, no actúa.

### Respuesta técnica
El parámetro `read_only` es un **invariante** del sistema (se valida al cargar la
config). El MVP solo lee archivos de log; nunca se conecta a infraestructura
productiva ni ejecuta cambios.

### Alternativas consideradas
- Permitir acciones automáticas o sugeridas sobre la infraestructura.

### Por qué no se eligieron
Actuar sobre producción es riesgoso y excede el alcance de un MVP de tesis;
queda como trabajo futuro.

### Relación con la tesis
Delimita el alcance de forma responsable y defendible ante el jurado.

---

## P-06

### Pregunta
¿Por qué empezar por una interfaz de línea de comandos (CLI)?

### Respuesta corta
Porque permite una demo funcional con el mínimo esfuerzo, enfocando el valor en
la lógica RAG.

### Respuesta técnica
Una CLI evita la complejidad de una web (servidor, frontend, estado) y permite
validar antes el núcleo del sistema. Una interfaz web mínima queda como mejora
opcional posterior.

### Alternativas consideradas
- Construir una interfaz web desde el inicio.

### Por qué no se eligieron
Añade complejidad sin aportar valor al objetivo central del MVP.

### Relación con la tesis
Aplica la Regla 10 (priorizar simplicidad) sin sacrificar la demostrabilidad.

---

## P-07

### Pregunta
¿Por qué la configuración usa YAML más un archivo `.env`?

### Respuesta corta
YAML para parámetros legibles y versionables; `.env` para secretos que no se
versionan.

### Respuesta técnica
`config/config.yaml` admite estructura anidada, listas y comentarios (ideal para
documentar parámetros en el propio archivo). Los secretos (API keys de fases
futuras) van en `config/.env`, excluido por `.gitignore`. Hay un único punto de
carga y validación (`src/config.py`).

### Alternativas consideradas
- Solo `.env`.
- JSON.
- TOML.
- `.ini` / ConfigParser.

### Por qué no se eligieron
- *Solo .env:* mal soporte de estructura anidada/listas.
- *JSON:* no admite comentarios.
- *TOML:* válido, pero YAML es más familiar en el ecosistema IA/MLOps.
- *.ini:* jerarquía y tipos limitados.

### Relación con la tesis
Soporta la reproducibilidad y la regla de "sin parámetros ocultos".

---

## P-08

### Pregunta
¿Por qué cada evento normalizado conserva `raw`, `source_file` y `line_number`?

### Respuesta corta
Para que las respuestas del asistente puedan **citar la evidencia exacta**.

### Respuesta técnica
Estos metadatos hacen que, en la fase RAG, el LLM pueda señalar el archivo y la
línea concreta que sustentan una afirmación. Sin ellos, la respuesta no sería
verificable (alucinación no detectable).

### Alternativas consideradas
- Guardar solo los campos parseados, descartando la línea original.

### Por qué no se eligieron
Perdería la citabilidad, que es un requisito de confiabilidad (RNF-05).

### Relación con la tesis
La **auditabilidad de las respuestas** es uno de los aportes diferenciales del MVP.

---

## P-09

### Pregunta
¿Por qué el parser usa solo la librería estándar de Python (sin dependencias pesadas)?

### Respuesta corta
Por simplicidad y reproducibilidad: el parseo se resuelve con `re`, `json` y
`datetime`.

### Respuesta técnica
La Fase 1 solo necesita expresiones regulares y manejo de fechas; añadir
librerías externas aumentaría la superficie de fallo sin beneficio. Las únicas
dependencias son PyYAML (config) y pytest (pruebas).

### Alternativas consideradas
- Usar librerías de parsing de logs de terceros.

### Por qué no se eligieron
Añaden complejidad y dependencias innecesarias para un formato bien acotado.

### Relación con la tesis
Aplica la Regla 10 (simplicidad) y facilita que el autor entienda cada línea.

---

## P-10

### Pregunta
¿Por qué la severidad del evento se deriva del código de estado HTTP?

### Respuesta corta
Porque el status code es la señal estándar y objetiva de éxito/error en HTTP.

### Respuesta técnica
Regla determinista: 5xx → `error`, 4xx → `warning`, resto → `info`. Al derivarla
(en lugar de leerla de cada fuente) se garantiza coherencia entre HAProxy e IIS y
se habilita filtrar/priorizar incidentes de forma uniforme.

### Alternativas consideradas
- Tomar un nivel de severidad textual propio de cada fuente.

### Por qué no se eligieron
HAProxy e IIS no exponen una severidad homogénea; derivarla del status es simple
y consistente.

### Relación con la tesis
Permite que el asistente distinga incidentes (errores) de tráfico normal.

---

## P-11

### Pregunta
¿Qué base de datos vectorial se usará para el RAG (p. ej. FAISS)?

### Respuesta corta
**Aún no decidido.** Se elegirá en la Fase 2 mediante un ADR; FAISS es candidato.

### Respuesta técnica
La elección (FAISS, Chroma u otra) se documentará cuando se implemente la
indexación, priorizando una solución **local y embebida** para el MVP (sin
infraestructura adicional). Esta entrada se completará al cerrar esa decisión.

### Alternativas consideradas (preliminar)
- FAISS (búsqueda vectorial local eficiente).
- ChromaDB.
- Elasticsearch.
- PostgreSQL + pgvector.

### Por qué no se eligieron (preliminar)
Para un MVP local, las opciones con servidor (Elasticsearch, Postgres) añaden
infraestructura; FAISS/Chroma permiten trabajar localmente. La decisión final se
registrará en un ADR de la Fase 2.

### Relación con la tesis
La base vectorial es el corazón de la recuperación semántica del flujo RAG.

> ⚠️ **Nota de honestidad técnica:** a la fecha (Fase 1) **no** se ha integrado
> ninguna base vectorial todavía. Esta pregunta queda como **prevista** y se
> actualizará a "Decidido" cuando exista el ADR correspondiente.

---

## P-12

### Pregunta
¿Por qué el proyecto adopta una metodología de revisión con cinco roles
("agentes": Arquitecto, Desarrollador, Documentador, Trazabilidad, Defensa)?
¿No contradice la regla de "no crear agentes complejos todavía"?

### Respuesta corta
Porque son **roles de revisión del proceso de desarrollo** (checklists), no
agentes de software; aportan calidad sistemática y defendibilidad. No
contradicen nada: la prohibición aplica al *producto*, no al *método*.

### Respuesta técnica
Cada cambio se mira desde cinco perspectivas (R13) y solo se considera "Hecho"
(R14) tras pasar las cinco revisiones. Esto reduce puntos ciegos: el Arquitecto
cuida la coherencia del diseño, el Desarrollador la calidad/tests, el
Documentador la sincronía doc↔código, el de Trazabilidad los vínculos
OE↔RF↔componente↔ADR↔pregunta, y el Tutor de Defensa la defendibilidad.

### Qué problema resuelve
Evita que cambios pasen sin documentación, sin trazabilidad o sin estar
preparados para la defensa; convierte las reglas en un control repetible.

### Alternativas consideradas
- Revisión informal/ad-hoc.
- Una sola checklist plana sin roles.
- Implementar agentes de software de revisión reales.

### Por qué no se eligieron
- *Ad-hoc:* no es trazable ni repetible.
- *Checklist plana:* funciona pero es menos pedagógica que cinco perspectivas.
- *Agentes de software reales:* exceden el alcance del MVP y chocarían con
  ADR-005 (solo-lectura) y con "no agentes complejos todavía".

### Qué pasa si se cambia este parámetro
Si se **reducen** los roles/revisiones, baja el coste por cambio pero aumenta el
riesgo de divergencia y de puntos ciegos. Si se **aumentan**, sube la calidad
pero también la burocracia (mitigable escalando el rigor al tamaño del cambio).

### Cómo se evalúa
Un cambio "pasa" si su cierre (formato de 8 apartados, R18) evidencia las cinco
revisiones y el banco de defensa queda actualizado.

### Limitaciones
Al desempeñar los cinco roles una sola persona/asistente, las revisiones **no
son independientes** (no hay separación real de responsables): es control de
calidad interno, no auditoría externa.

### Relación con la tesis
Refuerza dos atributos evaluables del proyecto: **trazabilidad** (RNF-03) y
**defendibilidad/calidad** (RNF-08). Vínculo R17: OE5 · RNF-03/RNF-08 · proceso ·
ADR-009 · esta P-12.

---

## P-13

### Pregunta
¿Por qué se diseñó un esquema normalizado de eventos en lugar de procesar cada
log en su formato original?

### Respuesta corta
Para que todo el sistema trate los eventos de forma **uniforme y agnóstica a la
fuente**, sin duplicar lógica por cada tipo de log.

### Respuesta técnica
HAProxy (HTTP log) e IIS (W3C) tienen formatos y campos distintos. Mapearlos a un
**evento común de 13 campos** (`src/schema.py`, ADR-010) permite que las fases
siguientes (chunking, indexación, recuperación) operen sobre una sola estructura.
El esquema es **fijo** (las claves siempre presentes; la ausencia se expresa con
`null`), lo que hace la salida predecible y diff-eable. Cinco campos núcleo
(`source`, `severity`, `source_file`, `line_number`, `raw`) garantizan identidad,
clasificación y **citabilidad**.

### Alternativas consideradas
- Procesar cada fuente con su propio formato hasta el final del pipeline.
- Almacenar solo texto plano sin estructura.
- Un esquema flexible sin claves fijas (omitir las ausentes).

### Por qué no se eligieron
- *Por fuente:* duplicaría la lógica aguas abajo y dificultaría añadir fuentes.
- *Texto plano:* impediría filtrar/clasificar (p. ej. por severidad o status).
- *Claves omitidas:* complicaría el consumo y los diffs; preferimos `null` explícito.

### Impacto si se modifica el esquema
Añadir, renombrar o quitar un campo **rompe** el contrato de salida: obliga a
actualizar parsers, `tests/test_schema.py` y, en fases futuras, a **reindexar**.
Por eso todo cambio de esquema exige un nuevo ADR (control de versión del contrato).

### Cómo se valida
`tests/test_schema.py` verifica el orden canónico de claves y la derivación de
severidad; `tests/test_parse_logs.py` confirma que la salida real contiene los
campos núcleo. (15 pruebas en verde a la fecha.)

### Limitaciones
El esquema modela hoy **logs de acceso HTTP**; no representa aún métricas ni
trazas distribuidas. Asume que los timestamps del log ya están en `timezone`.

### Relación con la tesis
Es la base (OE1, RF-03) sobre la que se apoya la recuperación con **citas
verificables** (RNF-05), uno de los aportes diferenciales del MVP.

---

## P-14

### Pregunta
¿Por qué unos campos del evento son obligatorios (no nulos) y otros opcionales?

### Respuesta corta
Porque hay un **mínimo imprescindible** para identificar, clasificar y **citar**
un evento; el resto depende de la fuente y puede no existir.

### Respuesta técnica
Cinco campos son **núcleo no nulo**: `source` (identidad de la fuente),
`severity` (clasificación, derivada del status), y la tríada de **citabilidad**
`source_file` + `line_number` + `raw`. `timestamp` siempre está presente como
clave pero puede ser `null` si la fecha no es parseable (no se descarta el evento
por ello, salvo política `skip`). Los campos HTTP/red (`client_ip`, `method`,
`path`, `status_code`, `bytes`, `duration_ms`, `backend`) son **opcionales**:
existen como clave pero valen `null` cuando la fuente no los provee (p. ej.
`backend` es `null` en IIS; `bytes` es `null` con los campos W3C por defecto).

### Alternativas consideradas
- Hacer todos los campos obligatorios.
- Hacer todos los campos opcionales (incluso los de cita).

### Por qué no se eligieron
- *Todos obligatorios:* imposible, ya que cada fuente expone un subconjunto
  distinto (forzaría valores inventados).
- *Todos opcionales:* perdería la garantía de **citabilidad** (RNF-05): sin
  `source_file`/`line_number`/`raw` no se podría apuntar a la evidencia.

### Impacto si se modifica el esquema
Degradar un campo núcleo a opcional **rompe la citabilidad** o la clasificación;
promover un opcional a obligatorio rompería el parseo de la fuente que no lo trae.
Cualquiera de los dos cambios requiere ADR y revisión de los parsers.

### Cómo se valida
Las pruebas comprueban que los campos núcleo aparecen siempre y que `severity`
se deriva correctamente; el modo `keep` se prueba para confirmar que una línea no
parseable conserva `raw`/`line_number` con el resto en `null`.

### Limitaciones
La frontera obligatorio/opcional está pensada para logs HTTP; una fuente futura
podría necesitar un campo núcleo distinto (se resolvería con `attributes` + ADR).

### Relación con la tesis
Equilibra **rigor** (garantías mínimas para citar y clasificar) con
**flexibilidad** (tolerar datos ausentes), alineado con RF-03 y RNF-05.

---

## P-15

### Pregunta
¿Cómo permite este esquema soportar nuevas fuentes de eventos en el futuro
(p. ej. syslog, eventos de aplicación, health-checks)?

### Respuesta corta
Añadiendo un valor al **enum `source`** y un parser que cumpla el mismo contrato;
los campos que no apliquen quedan en `null` y se conserva siempre la evidencia.

### Respuesta técnica
La extensibilidad se apoya en cuatro mecanismos (ADR-010):
1. **Enum `source` ampliable** (`haproxy`, `iis`, → `syslog`, `app`, …).
2. **Mismo contrato de parser:** `parse_line() -> (status, event)`, de modo que
   el orquestador no cambia.
3. **Campos HTTP nullable:** una fuente no-HTTP deja `method`/`path`/`status_code`/
   `backend` en `null` y se apoya en `severity` + `raw`.
4. **Citabilidad invariante:** `source_file`/`line_number`/`raw` se mantienen
   siempre. Para datos estructurados propios de la fuente se añadirá un campo
   opcional `attributes` (objeto) mediante un **ADR futuro** (no se crea aún:
   YAGNI / Regla 10).

### Alternativas consideradas
- Crear ya el campo `attributes` genérico.
- Subclasificar el esquema por tipo de fuente desde el inicio.

### Por qué no se eligieron
- *`attributes` ahora:* no hay aún una fuente que lo requiera; añadirlo sería
  complejidad especulativa (YAGNI).
- *Subclases por fuente:* reintroduciría la heterogeneidad que el esquema común
  busca eliminar.

### Impacto si se modifica el esquema
Introducir `attributes` será **retrocompatible** (campo opcional nuevo, default
`null`/`{}`), pero igualmente requerirá ADR, pruebas y posible reindexado de lo
ya procesado.

### Cómo se valida
Cuando se añada una fuente, se replicará el patrón de pruebas de Fase 1 (un test
por parser + integración) verificando que produce eventos conformes al esquema.

### Limitaciones
Mientras no exista `attributes`, los detalles específicos de una fuente no-HTTP
solo viven en `raw` (texto), no en campos consultables de forma estructurada.

### Relación con la tesis
Demuestra un **diseño extensible** y defendible: el MVP cubre HAProxy/IIS pero la
arquitectura admite crecer sin reescribir el pipeline (OE1, escalabilidad del enfoque).

---

## P-16

### Pregunta
¿Cómo se garantiza que el parser HAProxy realmente cumple el contrato del
esquema normalizado (ADR-010) y no solo "que parsea"?

### Respuesta corta
Con un **test de conformidad dedicado** (`tests/test_adr010_conformance.py`) que
verifica el contrato, separado de los tests de parseo funcional.

### Respuesta técnica
Hay dos niveles de prueba: (1) `test_haproxy_parser.py` valida que las líneas se
parsean (campos correctos, casos 503/vacía/corrupta); (2)
`test_adr010_conformance.py` valida el **contrato ADR-010** sobre el evento
resultante: las 13 claves presentes y en orden, los 5 campos núcleo no nulos, la
severidad derivada del status, que un opcional sin dato quede en `null` sin
omitir la clave, y que el evento sea serializable a JSON sin pérdida. Además, el
script `examples/demo_haproxy_parser.py` evidencia el flujo
`log → parse_line() → evento → JSON` de forma visual.

### Alternativas consideradas
- Confiar solo en los tests de parseo funcional.
- Validación con un JSON Schema externo.

### Por qué no se eligieron
- *Solo funcionales:* comprueban "que parsea", no que se respete el contrato del
  esquema (orden de claves, no-nulos, nulos explícitos).
- *JSON Schema externo:* añade dependencia e infraestructura; para el MVP, los
  asserts en pytest son más simples y suficientes (Regla 10). Queda como mejora.

### Impacto si se modifica el esquema
Si alguien cambia `EVENT_FIELDS` o un parser deja de poblar un campo núcleo, el
test de conformidad **falla de inmediato**, impidiendo divergencia silenciosa
entre el código y ADR-010 (refuerza R8).

### Cómo se valida
`python -m pytest -q` ejecuta ambos niveles (21 pruebas en verde a la fecha). La
demostración visual: `python -m examples.demo_haproxy_parser`.

### Limitaciones
El test de conformidad cubre hoy la fuente HAProxy; cuando se añadan otras
fuentes habrá que replicar el patrón de conformidad para cada una.

### Relación con la tesis
Convierte ADR-010 de un documento en un **contrato ejecutable y verificable**,
reforzando la defendibilidad (RNF-08) y la trazabilidad (RF-03).

---

## P-17

### Pregunta
En el evento normalizado de IIS, campos como `backend` y `bytes` aparecen en
`null`. ¿Eso no rompe el esquema ADR-010? ¿Cómo se valida su conformidad?

### Respuesta corta
No lo rompe: el esquema es **fijo con valores nullable**. IIS no tiene concepto
de `backend` y el set W3C por defecto no incluye `sc-bytes`, así que esas claves
existen pero valen `null`. Un test de conformidad lo verifica.

### Respuesta técnica
ADR-010 define un esquema de **13 claves siempre presentes**; la ausencia de dato
se expresa con `null`, nunca omitiendo la clave. Esto permite que dos fuentes
heterogéneas (HAProxy e IIS) produzcan **la misma estructura**: HAProxy rellena
`backend` (`be_api/web01`) y `bytes`; IIS los deja en `null`. Los 5 campos núcleo
(`source`, `severity`, `source_file`, `line_number`, `raw`) sí están garantizados
no nulos en ambas. La conformidad se valida en
`tests/test_adr010_conformance.py` con una sección IIS dedicada (Fase 1.3):
13 claves en orden, núcleo no nulo, severidad derivada de `sc-status`,
`backend`/`bytes` nulos pero presentes, `path` = `cs-uri-stem`(+`cs-uri-query`)
y serialización JSON sin pérdida.

### Alternativas consideradas
- Omitir del JSON las claves que IIS no tiene.
- Definir un esquema distinto por fuente.

### Por qué no se eligieron
- *Omitir claves:* cada fuente produciría JSON con distinta forma, complicando el
  consumo aguas abajo (chunking/indexación) y los diffs.
- *Esquema por fuente:* reintroduce la heterogeneidad que ADR-003 elimina.

### Impacto si se modifica el esquema
Si IIS empezara a exportar `sc-bytes`, bastaría con mapearlo (deja de ser `null`)
sin cambiar el contrato. Quitar una clave del esquema sí rompería ambas fuentes.

### Cómo se valida
`python -m pytest -q` (28 pruebas en verde; 13 de ellas de conformidad ADR-010,
repartidas entre HAProxy e IIS). El test
`test_iis_backend_y_bytes_nulos_pero_presentes` cubre exactamente este caso.

### Limitaciones
El mapeo IIS depende de las columnas declaradas en la directiva `#Fields:`; si un
servidor emite un conjunto de campos distinto, algunos valores podrían quedar en
`null` aunque existieran bajo otro nombre.

### Relación con la tesis
Demuestra que la **unificación de fuentes heterogéneas** (RF-03) es real y
verificable, no solo declarativa: dos formatos muy distintos producen el mismo
contrato citable.

---

## P-18

### Pregunta
¿Por qué se decidió implementar primero la normalización de eventos antes que las
técnicas de IA (embeddings, RAG, LLM)?

### Respuesta corta
Porque la calidad de los resultados de un sistema RAG depende directamente de la
calidad y consistencia de los datos de entrada. La normalización permitió
establecer un **contrato común verificable** antes de incorporar componentes de
inteligencia artificial.

### Respuesta técnica
Un sistema RAG es tan bueno como los datos que recupera: si los eventos llegan en
formatos heterogéneos (HAProxy vs IIS), incompletos o ambiguos, los embeddings
codifican ruido y la recuperación degrada — "garbage in, garbage out". Al
normalizar primero (ADR-003/ADR-010) se obtuvo un **esquema común de 13 campos**,
con severidad coherente y metadatos de **citabilidad** (`source_file`,
`line_number`, `raw`). Ese contrato es además **ejecutable y verificable** (tests
de conformidad ADR-010, 28 pruebas en verde), de modo que la base sobre la que se
construirá la IA está validada **antes** de añadir complejidad. También reduce el
riesgo del proyecto: las decisiones de IA (Fase 2A) se toman sobre datos estables.

### Alternativas consideradas
- Empezar directamente por embeddings/RAG sobre los logs crudos.
- Normalizar "lo justo" y dejar el resto al LLM.

### Por qué no se eligieron
- *RAG sobre crudos:* mezcla formatos, dificulta el filtrado por metadatos y
  destruye la citabilidad estructurada; los fallos serían difíciles de atribuir.
- *Normalizar mínimo:* trasladaría el trabajo de limpieza al LLM (más coste, menos
  control, más alucinación).

### Impacto si se modifica el esquema
Como toda la IA se construye sobre el contrato normalizado, cambiarlo obliga a
reprocesar y reindexar; por eso se versiona vía ADR (ADR-010).

### Cómo se valida
Tests de conformidad del esquema (`tests/test_adr010_conformance.py`) y de
parseo; la normalización es reproducible y auditable antes de tocar IA.

### Limitaciones
Invertir esfuerzo temprano en normalización retrasa la primera demo "vistosa" de
IA; se asume conscientemente a cambio de una base sólida y defendible.

### Relación con la tesis
Es la tesis central del enfoque: **primero datos confiables, luego IA**. Sustenta
la confiabilidad (RNF-05) y la defendibilidad (RNF-08) del MVP.

---

## P-19

### Pregunta
¿Por qué se eligió un chunking por **ventana de N eventos con solape** y no otra
estrategia?

### Respuesta corta
Porque equilibra **contexto** (correlacionar eventos vecinos de un incidente) y
**precisión/citabilidad**, con tamaños de chunk predecibles para el embedder.

### Respuesta técnica
Los datos son eventos cortos y estructurados, no prosa. Un incidente se entiende
en contexto (una ráfaga de 503), así que agrupar N eventos consecutivos con un
solape (~20 %) preserva la correlación y evita cortar una ráfaga en el borde.
Frente al chunking temporal, la ventana por conteo da chunks **homogéneos** (las
ráfagas no inflan un chunk), lo que controla coste y longitud para el embedder.
Cada chunk guarda metadatos de rango (archivo, líneas, timestamps) para mantener
la citabilidad. Ver ADR-011.

### Alternativas consideradas
Un evento = un chunk; ventana temporal fija; por tokens; chunking semántico.

### Por qué no se eligieron
Evento único pierde contexto; ventana temporal produce chunks desiguales;
por-tokens es innecesario con eventos cortos; semántico añade complejidad sin
beneficio claro (Regla 10).

### Impacto si se cambia el parámetro
↑N → menos chunks, más contexto, menor precisión y más coste por chunk; ↑solape →
más redundancia y más vectores. Cambiarlos obliga a reindexar.

### Cómo se valida
Inspección manual de chunks + recall sobre consultas de incidente de ejemplo.

### Limitaciones
La ventana por conteo ignora huecos temporales largos; podría unir periodos
distantes (mitigable con corte por salto temporal a futuro).

### Relación con la tesis
Define la unidad de evidencia que el RAG recuperará y citará; conecta la
normalización (ADR-010) con la recuperación (ADR-014).

---

## P-20

### Pregunta
¿Por qué embeddings **locales** y concretamente `all-MiniLM-L6-v2`?

### Respuesta corta
Por **privacidad** (los logs no salen del equipo), **coste cero**,
**reproducibilidad** y rapidez; MiniLM es un baseline sólido y ligero.

### Respuesta técnica
Los logs operativos pueden contener datos sensibles (IPs, rutas); con embeddings
locales ningún dato se envía a terceros, coherente con el espíritu de ADR-005.
`all-MiniLM-L6-v2` (384 dimensiones) corre en CPU, es rápido y suficiente para
recuperación semántica de un corpus pequeño, y al no requerir API key cualquiera
puede reproducir la tesis. Ver ADR-012.

### Alternativas consideradas
APIs de embeddings (OpenAI, Cohere); modelos locales grandes (e5/bge-large);
`fastembed` (ONNX, sin PyTorch).

### Por qué no se eligieron
Las APIs implican enviar logs a terceros (privacidad) y coste/dependencia; los
modelos grandes piden más RAM/tiempo sin beneficio claro a esta escala;
`fastembed` queda como alternativa ligera reconsiderable sin cambiar el diseño.

### Impacto si se cambia el parámetro
Cambiar de modelo cambia la **dimensión** y **obliga a reindexar**; la métrica
debe ser coherente con el modelo (coseno).

### Cómo se valida
Relevancia cualitativa de la recuperación sobre consultas de ejemplo (sin
benchmark formal en el MVP).

### Limitaciones
MiniLM es de lenguaje general, no específico de logs; la normalización previa
mitiga esto al dar vocabulario consistente.

### Relación con la tesis
Hace el sistema **privado y reproducible**, atributos valiosos para defender un
MVP de operaciones.

---

## P-21

### Pregunta
¿Por qué se eligió **Chroma** como vector store y no FAISS (u otros)?
*(Comparativa lado a lado en [P-23](#p-23).)*

### Respuesta corta
Porque Chroma guarda **vectores + metadatos + persistencia** juntos y los
devuelve en la consulta, lo que da **citabilidad** y simplicidad sin servidor;
FAISS es solo índice y exigiría más pegamento a una escala que no lo necesita.

### Respuesta técnica
El requisito diferencial es citar la evidencia (RNF-05): Chroma almacena junto a
cada vector sus metadatos (`source_file`, `line_number`, rango temporal,
`severity`) y permite **filtrado por metadatos** nativo (útil para la
recuperación acotada de ADR-014), todo local y persistente sin desplegar
infraestructura. FAISS es excelente para ANN a gran escala pero **no gestiona
metadatos**: habría que mantener un mapa id→metadato aparte. A la escala del MVP
(miles de chunks) la simplicidad de Chroma gana (Regla 10). Ver ADR-013.

### Alternativas consideradas
FAISS, Qdrant, Elasticsearch, PostgreSQL + pgvector.

### Por qué no se eligieron
FAISS no trae metadatos (más código); Qdrant/Elasticsearch requieren servidor;
pgvector exige PostgreSQL operativo. Todas añaden infraestructura o trabajo sin
beneficio a esta escala. **FAISS es la opción a reconsiderar si el volumen crece.**

### Impacto si se cambia el parámetro
Cambiar de backend, de métrica o de dimensión de embeddings obliga a reconstruir
el índice.

### Cómo se valida
Correctitud del top-k devuelto y latencia sobre el corpus local de ejemplo.

### Limitaciones
Chroma no apunta a escala masiva ni alta concurrencia; en producción a gran
volumen se migraría a FAISS/Qdrant.

### Relación con la tesis
Sostiene la **recuperación con citas** que distingue al MVP, minimizando
infraestructura. Cierra la pregunta abierta P-11.

---

## P-22

### Pregunta
¿Por qué una recuperación **top-k densa con filtros de metadatos** y no algo más
sofisticado (híbrido, re-ranking)?

### Respuesta corta
Porque es el núcleo estándar de RAG, simple y suficiente para el MVP, y el
filtrado por metadatos aprovecha la estructura del esquema para acotar como lo
haría un operador.

### Respuesta técnica
Las consultas de operación suelen venir acotadas en tiempo/severidad/backend. Con
los metadatos de cada chunk (ADR-011) y el filtrado nativo de Chroma (ADR-013) se
hace **pre-filtrado + top-k denso** por coseno, sin dependencias nuevas. Es un
baseline medible sobre el que decidir, con datos, si vale la pena añadir
complejidad. Ver ADR-014.

### Alternativas consideradas
Recuperación híbrida (BM25 + densa); MMR (diversidad); re-ranking con cross-encoder.

### Por qué no se eligieron
Híbrido y re-ranking mejoran calidad pero suben complejidad y coste; MMR ayuda si
hay redundancia, aún no demostrada. Se dejan como mejoras evaluables tras medir el
baseline (evitar complejidad prematura).

### Impacto si se cambia el parámetro
↑`top_k` → más recall pero más ruido y más tokens al LLM; ↑`score_threshold` →
menos chunks pero riesgo de quedarse sin contexto; filtros mal puestos pueden
excluir evidencia válida.

### Cómo se valida
Precisión@k sobre un conjunto pequeño de consultas de incidente con respuesta
conocida.

### Limitaciones
La recuperación densa pura puede fallar con términos exactos raros (IDs, códigos)
donde lo léxico ayudaría; por eso el híbrido queda señalado como mejora futura.

### Relación con la tesis
Define cómo se selecciona la evidencia que sustentará las respuestas citadas
(RNF-05), manteniendo el MVP simple y defendible.

---

## P-23

### Pregunta
¿Por qué Chroma y no FAISS? (comparativa directa)

> Amplía **P-21** con una comparación lado a lado. La decisión y su contexto
> completo están en **ADR-013**.

### Respuesta corta
Porque a la escala del MVP lo que importa es **citabilidad + simplicidad**, y
Chroma trae metadatos y persistencia integrados; FAISS es más rápido a gran
escala pero "solo vectores", y obligaría a construir alrededor lo que Chroma ya
da hecho.

### Respuesta técnica (comparativa)

| Criterio | **Chroma (elegido)** | **FAISS (alternativa)** |
|---|---|---|
| Naturaleza | Base vectorial con documentos + metadatos | Librería de índices ANN (solo vectores) |
| Metadatos / citabilidad | **Integrados**: devuelve `source_file`, `line_number`, rango temporal con cada resultado | Hay que mantener un **mapa id→metadato** aparte |
| Filtrado por metadatos | **Nativo** (clave para ADR-014) | No; se implementa manualmente |
| Persistencia | **Integrada** (en disco) | Manual (serializar índice + sidecar) |
| Escala / velocidad | Suficiente para miles de chunks | **Superior** a gran escala (millones) |
| Infraestructura | Local, embebido, sin servidor | Local, sin servidor |
| Esfuerzo de integración (MVP) | **Bajo** | Medio-alto (pegamento de metadatos) |

### Alternativas consideradas
FAISS, Qdrant, Elasticsearch, pgvector (ver ADR-013/P-21).

### Por qué no se eligió FAISS
A la escala del MVP (miles de chunks) su ventaja de velocidad no se necesita, y
su falta de gestión de metadatos añadiría código sin beneficio. **Es la opción a
reconsiderar si el volumen crece** a millones de vectores.

### Impacto si se cambia
Migrar a FAISS implicaría externalizar los metadatos de citabilidad y reconstruir
el índice; el resto del pipeline (chunks con metadatos) no cambiaría.

### Cómo se evalúa
Correctitud del top-k y latencia sobre el corpus local; si la latencia dejara de
ser aceptable al crecer, se reevaluaría FAISS.

### Limitaciones
Chroma no apunta a escala masiva ni alta concurrencia (ver P-21).

### Relación con la tesis
La citabilidad de la evidencia (RNF-05) es un aporte diferencial; Chroma la hace
barata. Cierra definitivamente P-11.

---

## P-24

### Pregunta
¿Por qué el chunker agrupa los eventos **por archivo de origen** y conserva
**metadatos de rango** (líneas y timestamps) en cada chunk?

### Respuesta corta
Para que cada chunk sea **coherente** (misma fuente, eventos contiguos) y
**citable** (se sabe exactamente qué líneas y qué intervalo de tiempo contiene).

### Respuesta técnica
El chunker (ADR-011) recorre cada archivo `*.events.jsonl` por separado y agrupa
**N eventos consecutivos con solape**. Agrupar por archivo evita mezclar fuentes
distintas (HAProxy/IIS) o periodos no contiguos en un mismo chunk, lo que
mantendría coherencia semántica para el futuro embedding. Cada chunk guarda
`source_file`, `line_start`/`line_end`, `ts_start`/`ts_end`, `n_events`, conteo de
`severities` y la lista de líneas de evento incluidas. Estos metadatos permiten
que, en la fase RAG, una respuesta apunte al **rango de evidencia exacto**
(RNF-05) y que la recuperación pueda **filtrar por tiempo/severidad** (ADR-014).

### Alternativas consideradas
- Chunk global mezclando todos los archivos/fuentes.
- Chunks sin metadatos de rango (solo texto).

### Por qué no se eligieron
- *Global mezclado:* rompería la coherencia (interleaving de fuentes) y la
  contigüidad temporal.
- *Sin metadatos:* perdería la citabilidad y el filtrado, núcleo del valor del MVP.

### Impacto si se cambia un parámetro
`chunk_size`/`chunk_overlap` cambian cuántos eventos abarca cada chunk y su
solape; modificarlos exige **re-chunkear** (y, en fases siguientes, reindexar).

### Cómo se valida
`tests/test_chunker.py` verifica la ventana/solape, los metadatos de rango, la
cobertura de líneas y que la salida sea JSONL válido.

### Limitaciones
La ventana por conteo no corta en saltos temporales largos; un chunk podría
abarcar un intervalo amplio si hay huecos (mejora futura: corte por tiempo).

### Relación con la tesis
Conecta la normalización (ADR-010) con la recuperación citable (ADR-014): el
chunk es la **unidad de evidencia** del sistema.

---

## P-25

### Pregunta
¿Cómo se prueba el Embedder sin depender del modelo real (que pesa cientos de MB
y requiere descarga)?

### Respuesta corta
**Separando la lógica de la dependencia pesada:** la orquestación recibe una
**función de codificación inyectada** (`encode_fn`); en producción es el modelo
real, en los tests es una función falsa determinista. Así las pruebas son
rápidas, **offline** y reproducibles.

### Respuesta técnica
`src/embedder.py` separa dos cosas: (1) `Embedder`, que carga
`sentence-transformers` con **import perezoso** (solo al usarse de verdad); y (2)
la lógica pura `embed_chunks(chunks, encode_fn, model_name)` y
`build_embedding_record(...)`, que **no importan** la librería. Los tests
(`tests/test_embedder.py`) inyectan una `encode_fn` falsa (vector determinista de
dimensión 3) y validan: un registro por chunk, herencia de metadatos, el esquema
del registro, el caso de texto vacío y la detección de desajustes vector↔chunk.
El flujo con el modelo real se valida de forma demostrativa (la CLI imprime la
dimensión 384). Esto aplica un patrón de **inversión de dependencias** clásico,
clave para testear componentes de IA de forma barata.

### Alternativas consideradas
- Cargar el modelo real en cada test.
- Hacer mock del módulo `sentence_transformers` con `unittest.mock`.

### Por qué no se eligieron
- *Modelo real en tests:* lento, requiere red/descarga, frágil en CI; rompe la
  reproducibilidad.
- *Mock del módulo:* funciona, pero es más opaco que inyectar una función simple;
  la inyección hace explícito el contrato (`textos -> vectores`).

### Impacto si se cambia un parámetro
Cambiar `embedding_model` cambia la **dimensión** del vector real y obliga a
reindexar; los tests de lógica no se ven afectados (usan dimensión arbitraria).

### Cómo se valida
`python -m pytest -q` (48 pruebas, offline). Demostración real:
`python -m src.embed_chunks` (imprime `Dimensión = 384` y escribe
`*.embeddings.jsonl`).

### Limitaciones
Las pruebas no verifican la **calidad semántica** de los embeddings reales (eso
exige un set de evaluación); validan la **integración y el contrato**, no la
relevancia. La calidad se medirá al evaluar la recuperación (Fase 3).

### Relación con la tesis
Demuestra ingeniería de calidad sobre un componente de IA: el sistema es
**testeable y reproducible** sin coste de cómputo, atributo defendible (RNF-08).

---

## P-26

### Pregunta
¿Cómo se guardan los metadatos en Chroma (que solo admite escalares) y por qué se
indexa con **upsert** en lugar de `add`?

### Respuesta corta
Los metadatos se **aplanan** a escalares (los conteos de severidad pasan a
`sev_info`/`sev_warning`/`sev_error`); y se usa **upsert** para que **reindexar
sea idempotente** (no duplica puntos, los actualiza por `chunk_id`).

### Respuesta técnica
Chroma solo acepta metadatos escalares (str/int/float/bool), no listas ni dicts.
El registro de embedding trae `severities` como dict, así que `to_chroma_metadata`
lo aplana a tres contadores enteros y sustituye `None` por `""`/`-1`. Esto, además
de cumplir la restricción, deja los campos **listos para filtrar** en la
recuperación (ADR-014): por `source_file`, rango de líneas, `ts_*` o severidad.
El `id` de cada punto es el `chunk_id`; `collection.upsert(...)` inserta o
**reemplaza** por id, de modo que volver a indexar el mismo corpus no crea
duplicados (verificado: 2 puntos tras dos ejecuciones). Como `document` se guarda
una referencia de cita legible `"archivo:linea_ini-linea_fin"`.

### Alternativas consideradas
- Guardar `severities` como cadena JSON en un solo campo.
- Usar `add` en vez de `upsert`.
- No guardar metadatos (solo vectores).

### Por qué no se eligieron
- *JSON en un campo:* no permitiría filtrar por severidad en Chroma.
- *`add`:* fallaría o duplicaría al reindexar; `upsert` es idempotente.
- *Sin metadatos:* rompería la citabilidad (RNF-05) y el filtrado futuro.

### Qué pasa si se cambia un parámetro
Cambiar `similarity_metric` o la **dimensión** del modelo de embeddings obliga a
**recrear** la colección; `collection_name`/`index_path` permiten separar o ubicar
distintos índices.

### Cómo se valida
`tests/test_vector_store.py` comprueba que los metadatos son escalares y que las
severidades se aplanan; `tests/test_index_embeddings.py` valida el flujo con un
**store falso** (sin chromadb) e incluye un test de **idempotencia** del upsert.
Demostración real: `python -m src.index_embeddings` (cuenta estable al repetir).

### Limitaciones
El aplanado fija las severidades a tres claves conocidas; una severidad nueva
requeriría añadir su columna. Chroma local no apunta a escala masiva (ver P-21/P-23).

### Relación con la tesis
Hace que el índice sea **citable y filtrable** (base de la recuperación con
evidencia, RNF-05) y **reproducible** (reindexar es seguro), sin infraestructura.

---

## P-27

### Pregunta
¿Cómo se convierte una **consulta textual** en **evidencia recuperada** sin usar
todavía un LLM?

### Respuesta corta
La consulta se **embebe** con el mismo modelo local que los chunks (ADR-012) y su
vector se compara por **similitud coseno** contra el índice Chroma (ADR-013),
devolviendo los **top-k** chunks más cercanos con su cita. Es **matemática de
vectores**, no generación: el LLM (Fase 4) aún no interviene.

### Respuesta técnica
El retriever (ADR-014, `src/retriever.py`) ejecuta una tubería de pasos puros y
auditables: (1) valida la consulta; (2) la **embebe** con `all-MiniLM-L6-v2`
(384-d) — el **mismo** modelo usado al indexar, condición para que las distancias
sean comparables; (3) opcionalmente construye un filtro `where` de metadatos
(`build_where`: por `source_file` y/o presencia de severidad); (4) pide a Chroma
los **top-k** vecinos (`store.query`); (5) convierte cada **distancia → score**
(`distance_to_score`: coseno → `1 - distance`), ordena por score descendente,
aplica `score_threshold` y asigna `rank`; (6) reconstruye las severidades desde
los campos planos `sev_*` y arma el resultado **citable** (`document`
= `archivo:linea_ini-fin`, `source_file`, `line_start/end`, `ts_*`). La salida es
una **lista de chunks con score y cita**, no una respuesta en prosa. La frontera
con el LLM es deliberada: aquí termina la **recuperación de evidencia**; el
ensamblado de prompt y la generación con citas son la Fase 4.

### Alternativas consideradas
- Búsqueda **léxica** (coincidencia de palabras / BM25) sobre el texto del log.
- Mandar la consulta y los logs **directamente a un LLM** sin recuperación previa.

### Por qué no se eligieron
- *Léxica pura:* no captura sinónimos ni paráfrasis ("caída del backend" vs
  "503 be_api down"); la búsqueda **densa** sí, por eso es el núcleo del RAG
  (lo léxico se reserva como mejora híbrida futura, ver P-22).
- *Todo al LLM:* es justo lo que el proyecto evita (ADR-001/P-01): sin recuperar
  primero, el modelo alucina y no puede citar evidencia real.

### Qué pasa si se cambia un parámetro
↑`top_k` → más evidencia recuperada (más recall, más ruido); ↑`score_threshold`
→ se descartan chunks poco similares (más precisión, riesgo de quedarse sin
contexto); un filtro de metadatos demasiado estricto → 0 resultados (no es un
error). Cambiar el **modelo de embeddings** rompería la comparabilidad y obliga a
reindexar.

### Cómo se evalúa
`tests/test_retriever.py` valida sin dependencias pesadas (inyectando `embed_fn`
y `store` falsos): la conversión distancia→score, el orden por score, el umbral,
la reconstrucción de severidades, los filtros y el flujo completo de `retrieve()`.
Demostración real: `python -m src.retrieve "errores 503 backend down" --top-k 3`.
(66 pruebas en verde a la fecha.)

### Limitaciones
La recuperación densa puede fallar con **términos exactos raros** (IDs, códigos)
donde lo léxico ayudaría; y la **calidad semántica** depende del modelo de
embeddings (no se mide con un benchmark formal en el MVP, solo cualitativamente).

### Relación con la tesis
Materializa la **primera mitad del RAG** (recuperar evidencia citable, RNF-05)
de forma **transparente y testeable**, dejando claro qué hace el sistema **antes**
de introducir un LLM. Vínculo R17: OE3 · RF-07/RF-08 · Retriever · ADR-014 · P-27.

---

## P-28

### Pregunta
¿Cómo se validó el pipeline con **logs reales** y qué desajustes revelaron frente
a los logs sintéticos?

### Respuesta corta
Se ejecutó el pipeline completo (parse→chunk→embed→índice, **sin LLM**) sobre el
corpus real del balanceador HAProxy. La validación destapó **tres desajustes** que
los samples sintéticos ocultaban: los logs venían **comprimidos** (`.gz`) y en
**subcarpetas por app**, el formato real traía **cabeceras capturadas** `{host}`
que rompían el parser, y un archivo "iis" era en realidad **HAProxy**. Se corrigió
todo (ADR-015) y se midió eventos/chunks/embeddings/tiempo de indexación.

### Respuesta técnica
El corpus real (logs de HAProxy de la USFQ) tiene 269 archivos. Al intentarlo
afloraron: (1) **compresión y estructura** — un `.log` vigente por app más decenas
de `.log-YYYYMMDD.gz` rotados, organizados en una subcarpeta por aplicación; (2)
**cabeceras capturadas** — el `capture request header` de HAProxy inserta uno o
dos bloques `{...}` (p. ej. `{api-account-devl.usfq.edu.ec}`) entre las colas y la
petición, y el regex del sample sintético no los preveía, de modo que **el 100 %
de las líneas reales caía como no parseable** (0 eventos con `on_parse_error=skip`);
(3) **nombre engañoso** — `app-portal-sitios-iis-devl` parecía IIS por el nombre,
pero su contenido es HAProxy (el "iis" es el *backend* Windows). La respuesta
(ADR-015): lectura `.gz` transparente con `gzip` (stdlib) y descubrimiento
recursivo multi-patrón (`src/ingest.py`); regex HAProxy tolerante a 0–2 bloques
`{...}` (retrocompatible); y tratar el corpus como HAProxy. Un arnés
(`src/validate_corpus.py`) mide cada etapa. Resultados en
`docs/91_VALIDACION_CORPUS.md`.

### Alternativas consideradas
- Descomprimir los `.gz` a disco en un paso previo y dejar el pipeline igual.
- Reescribir el parser con una gramática completa del log de HAProxy.
- Confiar en los samples sintéticos y posponer el corpus real.

### Por qué no se eligieron
- *Descomprimir a disco:* duplica datos y añade un paso manual frágil; `gzip` al
  vuelo es trivial (Regla 10).
- *Gramática completa:* excesivo para el MVP cuando basta admitir un bloque
  opcional en el patrón.
- *Posponer:* la tesis exige evidencia de que el sistema funciona con datos
  **reales**, no solo de juguete; validar temprano reduce riesgo.

### Qué pasa si se cambia un parámetro
Incluir `*.gz` en `file_patterns` (o activar `recursive`) multiplica el volumen
ingerido y, por tanto, eventos/chunks/embeddings y el **tiempo de indexación**;
`chunk_size`/`overlap` cambian cuántos chunks se generan por evento.

### Cómo se evalúa
`tests/test_ingest.py` (lectura `.gz`/plano, descubrimiento recursivo sin
duplicados) y `tests/test_haproxy_parser.py` (líneas reales con 1 y 2 bloques de
cabeceras capturadas). La medición end-to-end (eventos, chunks, embeddings,
tiempos) queda registrada y es reproducible con `python -m src.validate_corpus`.

### Limitaciones
El corpus actual es **HAProxy-only**: no hay un log **W3C-IIS real**, así que la
conformidad IIS sigue validada solo con el sample sintético. El corte por fecha
del rotado `.gz` y un benchmark de relevancia quedan como mejoras futuras.

### Relación con la tesis
Demuestra honestidad y robustez de ingeniería: el MVP se confronta con **datos
reales**, se documentan los desajustes y se corrigen de forma trazable (ADR-015).
Vínculo R17: OE1 · RF-01 · Ingesta · ADR-015 · P-28.

---

> **Mantenimiento (Reglas R12/R15):** cada cambio técnico relevante añade o
> actualiza una entrada aquí con formato tribunal (R16). Al tomar una decisión
> "Pendiente", cambiar su estado a "Decidido" y enlazar su ADR.
