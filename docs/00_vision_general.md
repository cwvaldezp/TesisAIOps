# 00 · Visión general

> Documento raíz: explica **qué** construimos, **por qué** y **hasta dónde**
> llega el MVP. Todo lo demás (arquitectura, flujos, parámetros) deriva de aquí.

---

## 1. Contexto y problema

Las plataformas de infraestructura web modernas combinan balanceadores
**HAProxy** (capa de entrada / proxy) y servidores **IIS** (aplicación). Cuando
hay un incidente operativo —latencia alta, errores 5xx, backend caído,
saturación de conexiones— el diagnóstico exige correlacionar manualmente logs
voluminosos y heterogéneos.

Problemas del enfoque manual:

- **Volumen:** miles a millones de líneas por hora.
- **Heterogeneidad:** formatos distintos (HAProxy HTTP log vs. IIS W3C).
- **Conocimiento tácito:** la interpretación depende del experto disponible.
- **Tiempo:** el MTTR (Mean Time To Resolve) crece con la búsqueda manual.

## 2. Propuesta

Un **asistente conversacional** que aplica **NLP + RAG + LLM** para que el
operador pregunte en lenguaje natural ("¿por qué hubo 503 entre las 14:00 y las
14:10?") y reciba una respuesta **fundamentada en las líneas de log reales**,
con citas verificables.

### ¿Por qué RAG y no solo un LLM?

- Un LLM **solo** alucina sobre datos que no vio y no conoce los logs concretos.
- **RAG** (Retrieval-Augmented Generation) recupera primero los fragmentos de
  log relevantes y se los entrega al LLM como contexto → respuestas **ancladas
  en evidencia** y **auditables** (se puede mostrar la línea exacta).

## 3. Objetivos

### Objetivo general
Construir un MVP de asistente que, a partir de logs HAProxy/IIS de ejemplo,
permita consultar incidentes en lenguaje natural y obtener respuestas
fundamentadas con citas a los logs.

### Objetivos específicos
1. **OE1** — Parsear logs HAProxy e IIS a un esquema normalizado común.
2. **OE2** — Trocear e indexar los logs en una base vectorial (embeddings).
3. **OE3** — Recuperar fragmentos relevantes ante una consulta en lenguaje natural.
4. **OE4** — Generar respuestas con un LLM que **citen** las líneas de origen.
5. **OE5** — Documentar arquitectura, flujos, parámetros y decisiones de forma
   trazable y defendible.

## 4. Alcance (in / out)

| In-scope (MVP) | Out-of-scope (futuro) |
|---|---|
| Logs locales de ejemplo (HAProxy, IIS) | Ingesta en streaming desde producción |
| Parsing + normalización | Conexión directa a infraestructura real |
| Indexación RAG local | Base vectorial distribuida / cloud a gran escala |
| Consulta NLP + respuesta con citas | Acciones correctivas automáticas |
| CLI o interfaz mínima | Autenticación / multiusuario robusto |
| Documentación y trazabilidad | Agentes autónomos complejos |

## 5. Usuarios y casos de uso

- **Operador / SRE de guardia:** investiga un incidente en curso.
- **Analista de soporte N2/N3:** revisa post-mortem qué ocurrió.
- **Tutor / jurado de tesis:** evalúa la solución y su defensa técnica.

Caso de uso principal (MVP):
> "Dado un conjunto de logs cargados, el operador hace una pregunta en lenguaje
> natural sobre un incidente y el asistente responde citando las líneas de log
> que sustentan la respuesta."

## 6. Criterios de éxito del MVP

- [ ] Se parsean correctamente logs HAProxy e IIS de ejemplo.
- [ ] Una consulta en lenguaje natural recupera fragmentos relevantes.
- [ ] La respuesta del LLM cita líneas de log reales (sin inventar).
- [ ] El sistema es reproducible siguiendo el manual técnico.
- [ ] Toda decisión y parámetro está documentado y es trazable.

## 7. Restricciones y principios

- **Seguridad:** no se actúa sobre infraestructura real; solo lectura de archivos.
- **Defendibilidad:** cada componente debe poder explicarse y justificarse.
- **Incrementalidad:** fases pequeñas y verificables; documentar antes de codificar.
- **Reproducibilidad:** parámetros externalizados y documentados.

## 8. Glosario

| Término | Definición |
|---|---|
| **HAProxy** | Balanceador de carga / proxy inverso; genera logs de peticiones. |
| **IIS** | Internet Information Services (servidor web de Microsoft). Logs W3C. |
| **NLP** | Procesamiento de Lenguaje Natural. |
| **LLM** | Large Language Model; genera texto a partir de un contexto. |
| **RAG** | Retrieval-Augmented Generation: recuperar evidencia + generar respuesta. |
| **Embedding** | Vector numérico que representa el significado de un texto. |
| **Chunk** | Fragmento de texto en que se trocea un log para indexarlo. |
| **Vector store** | Base de datos que indexa embeddings y busca por similitud. |
| **Retriever** | Componente que recupera los chunks más relevantes a una consulta. |
| **MTTR** | Mean Time To Resolve: tiempo medio de resolución de incidentes. |
| **MVP** | Minimum Viable Product: versión mínima demostrable. |
| **ADR** | Architecture Decision Record: registro de una decisión técnica. |

## 9. Documentos relacionados

- Trazabilidad de requisitos → [`01_trazabilidad.md`](01_trazabilidad.md)
- Arquitectura → [`02_arquitectura.md`](02_arquitectura.md)
- Flujos → [`03_flujos.md`](03_flujos.md)
- Parámetros → [`04_parametros_configuracion.md`](04_parametros_configuracion.md)
- Decisiones → [`05_bitacora_decisiones.md`](05_bitacora_decisiones.md)
