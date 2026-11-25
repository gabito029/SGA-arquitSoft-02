# Sprint 2: Implementación y validación de la arquitectura de software

**Curso:** IS488 Arquitectura de Software (UNSCH), 2026-II. **Docente:** Ing. Lizbeth Jaico Quispe.
**Proyecto:** SGA, Sistema de Gestión de Almacén con Firma Digital.
**Estado al 2026-11-25:** incrementos 001 y 002 implementados, probados e integrados en `main`.

> "En este sprint, los estudiantes llevarán a código la arquitectura documentada en el Sprint 1,
> implementando una primera versión funcional del proyecto." (enunciado del Sprint 2)

La arquitectura del Sprint 1 está en [`docs/`](../docs/), que es la fuente de verdad del proyecto y
no se modificó en este sprint. Las reglas para implementarla están en la
[constitución del proyecto](../.specify/memory/constitution.md) (v1.3.0). Las especificaciones de
cada incremento están en [`specs/`](../specs/).

Leyenda de estado: ✅ cumplido · ⏳ parcial o pendiente (con su motivo) · ⚠️ con una observación.

---

## 1. Actividades

| N.° | Actividad (texto del enunciado) | Cómo se cumplió | Evidencia | Estado |
|---|---|---|---|---|
| 1 | Implementar el estilo arquitectónico. | **Monolito modular** (ADR-001): una sola API FastAPI con ocho módulos de negocio que se comunican solo por sus servicios públicos, nunca por las tablas de otro módulo. `main.py` registra los routers de cada módulo. Una prueba automática impide que un módulo use la infraestructura de otro. | [`app/modules/`](../tecnologia/backend/app/modules/) · [`main.py`](../tecnologia/backend/app/main.py) · [`test_reglas_dependencia.py`](../tecnologia/backend/tests/unitarias/test_reglas_dependencia.py) · [Estilo arquitectónico](../docs/02-arquitectura-software/estilo-arquitectonico.md) | ✅ |
| 2 | Aplicar el enfoque o patrón arquitectónico (ejemplo: Clean Architecture, MVC). | **Clean Architecture dentro de cada módulo** (ADR-002): carpetas `dominio`, `aplicacion`, `infraestructura` y `presentacion`. El dominio es Python puro: la misma prueba de reglas de dependencia falla si importa FastAPI, SQLAlchemy, `cryptography`, ReportLab o el disco. | [`requests/`](../tecnologia/backend/app/modules/requests/) · [`signing/`](../tecnologia/backend/app/modules/signing/) · [`test_reglas_dependencia.py`](../tecnologia/backend/tests/unitarias/test_reglas_dependencia.py) · [Enfoque arquitectónico](../docs/02-arquitectura-software/enfoque-arquitectonico.md) | ✅ |
| 3 | Especificaciones SDD de las funcionalidades implementadas, incluyendo criterios de aceptación y tareas técnicas. | Con **Spec Kit**, cada incremento tiene `spec.md` (historias trazadas a HU y RF de `docs/`, criterios de aceptación verificables), `plan.md` (revisión de la constitución y desviaciones), `tasks.md` (tareas técnicas marcadas al completarse), contrato OpenAPI, modelo de datos y quickstart. | [001: flujo de solicitud](../specs/001-flujo-solicitud/) · [002: documento firmado](../specs/002-documento-firmado/) · [constitución](../.specify/memory/constitution.md) | ✅ |
| 4 | Endpoints REST funcionales y documentados con OpenAPI/Swagger. | Todos los endpoints están bajo `/api/v1`, con esquemas Pydantic de entrada y salida y sus respuestas de error (401, 403, 404, 409, 422). FastAPI publica Swagger UI en `/docs` y el esquema en `/openapi.json`. Los contratos de diseño están versionados por incremento. | [Swagger (local)](http://localhost:8080/docs) · [contrato 001](../specs/001-flujo-solicitud/contracts/openapi.yaml) · [contrato 002](../specs/002-documento-firmado/contracts/openapi.yaml) · [`router.py`](../tecnologia/backend/app/modules/requests/presentacion/router.py) | ✅ |
| 5 | Analizar el comportamiento de la base de datos y la estrategia de caché. | PostgreSQL 16 con migraciones Alembic, índices de las consultas críticas, paginación, bloqueo de filas (`SELECT … FOR UPDATE`) para el stock y disparadores de inmutabilidad. Caché TTL en memoria para el catálogo, sin contenedor nuevo. Se midió con y sin caché (p95 de 40,8 ms frente a 1 010 ms) y se analizaron `pg_stat`, el acierto de caché (99,99 %) y los planes de ejecución. El análisis encontró un Seq Scan en la bandeja y propone un índice. | [Análisis de BD y caché](../evidencias/README.md#análisis-de-la-base-de-datos-y-de-la-caché) · [`analisis-bd-cache-001.json`](../evidencias/EQ-04/analisis-bd-cache-001.json) · [migraciones](../tecnologia/backend/migrations/versions/) · [`cache_ttl.py`](../tecnologia/backend/app/modules/catalog/aplicacion/cache_ttl.py) | ✅ (el índice propuesto para la bandeja queda pendiente) |
| 6 | Aplicar principios SOLID y patrones de diseño cuando corresponda. | Los cinco principios SOLID y los patrones State, Repository, Unit of Work, Adapter, Strategy e inyección de dependencias, cada uno con su archivo, un fragmento de código y su motivo, relacionados con `docs/03-diseno-de-software`. | [SOLID y patrones](SOLID-y-patrones.md) · [Principios de diseño (docs)](../docs/03-diseno-de-software/diseno-interno/principios-de-diseno.md) | ✅ |
| 7 | Implementar pruebas automatizadas con Jest para validar las funcionalidades y reglas de negocio; se recomienda integrar estas pruebas en un flujo CI/CD mediante GitHub Actions, para automatizar su ejecución ante cada cambio en el código. | **Frontend:** 253 pruebas Jest (lógica, sesión, cliente de la API, componentes y páginas). **Backend:** 934 pruebas **pytest**, porque el backend es Python (ADR-011) y Jest es una herramienta de JavaScript; ver la nota de la sección 4. **GitHub Actions** ejecuta en cada push y cada pull request Ruff, pytest con cobertura, ESLint, `tsc`, Jest con cobertura y el build, y publica los reportes de cobertura como artefactos. | [`ci.yml`](../.github/workflows/ci.yml) · [pruebas del frontend](../tecnologia/frontend/tests/) · [pruebas del backend](../tecnologia/backend/tests/) | ✅ |
| 8 | Ejecutar pruebas basadas en los escenarios de atributos de calidad definidos en el Sprint 1, utilizando herramientas adecuadas como por ejemplo Postman, k6 (simular progresivamente hasta 2,000 usuarios virtuales concurrentes), Jest, entre otros. | Los escenarios EQ-01 a EQ-09 de `docs/` se probaron con pytest + httpx, pytest + `cryptography`, pytest + PostgreSQL, Postman/Newman, k6 y Jest. La prueba de estrés de k6 subió de forma progresiva hasta **2 000 VU**. Ver la sección 3. | [Evidencias](../evidencias/README.md) · [scripts k6](../tecnologia/pruebas/k6/) · [colección Postman](../tecnologia/pruebas/postman/sga-001.postman_collection.json) | ✅ en 7 de 9 escenarios · ⏳ EQ-05 y EQ-06 (sección 3) |

---

## 2. Entregables

| Entregable (texto del enunciado) | Cómo se cumplió | Evidencia | Estado |
|---|---|---|---|
| (a) Código fuente organizado según la arquitectura propuesta. | `tecnologia/backend` (FastAPI, ocho módulos con cuatro capas), `tecnologia/frontend` (React + TypeScript), `tecnologia/nginx` y `docker-compose.yml`: los contenedores del C4 nivel 2. Las reglas de dependencia se prueban en CI. | [`tecnologia/`](../tecnologia/) · [C4 nivel 2](../docs/04-modelo-c4/Nivel2-DiagramadeContenedores.md) · [C4 nivel 3](../docs/04-modelo-c4/Nivel3-DiagramadeComponentes.md) | ✅ |
| (b) Primera versión funcional del proyecto. | Flujo completo con `docker compose up --build -d`: registro y envío, conducto regular con firma Ed25519 en cada nivel, aprobación del almacén, despacho con bloqueo de stock, acta de recepción firmada, línea de tiempo y anulación (001). Además, documento oficial con sellos, revisión obligatoria antes de firmar, PDF firmado con código de verificación, PDF del acta y verificación de un PDF subido (002). | [README: cómo levantarlo](../README.md#cómo-levantarlo) · [quickstart 001](../specs/001-flujo-solicitud/quickstart.md) · [quickstart 002](../specs/002-documento-firmado/quickstart.md) · [ensayo SC-009](../evidencias/SC-009/LEEME.md) | ✅ |
| (c) Documentación de API mediante OpenAPI/Swagger. | Swagger UI generado por FastAPI en `/docs`, con cada endpoint, sus esquemas y sus errores. Contratos de diseño en `specs/*/contracts/openapi.yaml`. | [Swagger (local)](http://localhost:8080/docs) · [contrato 001](../specs/001-flujo-solicitud/contracts/openapi.yaml) · [contrato 002](../specs/002-documento-firmado/contracts/openapi.yaml) | ✅ |
| (d) Pruebas automatizadas con Jest y reporte de cobertura. | Jest con cobertura en el frontend: 253 pruebas, 100 % de líneas y 96,6 % de ramas en `src/logica`, `src/auth` y `src/api` (umbral 60 %). En el backend, pytest con cobertura: 934 pruebas, 97 % en total (umbral 60 % en los módulos críticos). Los dos reportes se generan en CI. | [cobertura Jest (HTML)](../evidencias/EQ-07/frontend-cobertura-html/index.html) · [cobertura pytest (HTML)](../evidencias/EQ-07/backend-cobertura-html/index.html) · [cobertura por módulo](../evidencias/EQ-07/cobertura-por-modulo-001.txt) | ✅ |
| (e) Evidencias y resultados de validación de los atributos de calidad. | Una carpeta por escenario en `evidencias/`, con el resumen, el método, la herramienta, la métrica objetivo, el resultado y si cumple. | [evidencias/README.md](../evidencias/README.md) | ✅ (con los pendientes de la sección 3) |

---

## 3. Escenarios de atributos de calidad (EQ-01 a EQ-09)

Los escenarios son los de
[`docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md`](../docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md).

| Escenario | Herramienta | Resultado | Estado |
|---|---|---|---|
| EQ-01 Seguridad | pytest + httpx; Newman | 536 de 536 intentos no autorizados rechazados (100 %); Newman 67 de 67 | ✅ [evidencia](../evidencias/EQ-01/) |
| EQ-02 Integridad | pytest + `cryptography` (Ed25519) | 001: 11 de 11 alteraciones detectadas. 002: el PDF tal cual da AUTENTICO, y con un byte cambiado o una cantidad firmada cambiada en la BD da ALTERADO | ✅ [evidencia](../evidencias/README.md#incremento-002-eq-02-con-el-pdf-verificable) |
| EQ-03 Consistencia del inventario | pytest + PostgreSQL | 3 de 3 corridas de despachos simultáneos sin diferencias de stock | ✅ [evidencia](../evidencias/EQ-03/) |
| EQ-04 Rendimiento | k6 (en lugar de Locust) | p95 de 40,8 ms con caché y de 1 010 ms sin caché, con 20 usuarios (objetivo < 2 s) | ✅ [evidencia](../evidencias/EQ-04/) |
| EQ-05 Usabilidad | Jest; Lighthouse | Formularios con 5 campos o menos (Jest). Lighthouse no se ejecutó | ⏳ Parcial |
| EQ-06 Disponibilidad | `docker kill` + Uptime Kuma | No se ejecutó: Uptime Kuma no está en `docker-compose.yml` | ⏳ Pendiente |
| EQ-07 Mantenibilidad | pytest-cov, Ruff, ESLint | Cobertura ≥ 60 % en los módulos críticos (97 a 100 %), 0 errores de lint | ✅ [evidencia](../evidencias/EQ-07/) |
| EQ-08 Trazabilidad | pytest + PostgreSQL; Newman | 6 de 6 pasos con usuario, rol, órgano y fecha; cadena de auditoría íntegra | ✅ [evidencia](../evidencias/EQ-08/) |
| EQ-09 Escalabilidad | k6 con `--scale api=2` | p95 de 58,8 ms (1 instancia) y de 48,2 ms (2 instancias) con 40 usuarios | ✅ [evidencia](../evidencias/EQ-09/) |
| Estrés hasta 2 000 VU (enunciado) | k6 `ramping-vus` | Llegó a 2 000 VU activos; punto de quiebre en unos 80 a 100 VU (~70 req/s); 0 errores. La corrida se interrumpió al 88 % del tiempo | ⚠️ [evidencia](../evidencias/ESTRES/) |

---

## 4. Herramientas de prueba: pytest en el backend y Jest en el frontend

El enunciado pide "pruebas automatizadas con **Jest**". Jest es un framework de JavaScript y
TypeScript, y el backend del SGA es **Python + FastAPI** por decisión del Sprint 1
(**ADR-011**, en [`docs/01-analisis-de-sistema/07-decisiones-arquitectonicas.md`](../docs/01-analisis-de-sistema/07-decisiones-arquitectonicas.md)).
Para respetar esa decisión, que es lo que el criterio fundamental evalúa:

- **Frontend (React + TypeScript): Jest**, con React Testing Library y reporte de cobertura. Cubre
  la lógica, la sesión, el cliente de la API, los componentes y las páginas.
- **Backend (Python): pytest**, el equivalente de Jest en Python, con `pytest-cov` para la
  cobertura, httpx para la API y PostgreSQL real para la integración. Es la herramienta que
  `docs/` define para EQ-01, EQ-02, EQ-03, EQ-07 y EQ-08.

Esta decisión está registrada en la constitución (v1.1.0, principio VI) como "ampliación
aprobada": Jest solo en el frontend, y el backend sigue con pytest. Usar Jest en el backend obligaría
a reescribirlo en Node.js y contradiría ADR-011.

---

## 5. Desviaciones de `docs/` y su estado

Todas están registradas en la constitución, en "Conflictos con docs/ y su resolución", y en el
"Complexity Tracking" de cada plan.

### Desviaciones temporales

| Id | Qué | Motivo | Estado al 2026-11-25 |
|---|---|---|---|
| DT-01 | En 001 la firma Ed25519 se verificaba solo con el endpoint de verificación, sin PDF (ADR-004, RF05, ADR-010) | Plazo del MVP de 5 días | ✅ **Cerrada** (constitución v1.3.0). El incremento 002 emite el PDF firmado del requerimiento y del acta y verifica un PDF subido (AUTENTICO o ALTERADO) |
| DT-02 | El entorno local usa HTTP en lugar de HTTPS (AC01) | HTTPS se configura junto con el despliegue | ⏳ **Abierta**, prorrogada en v1.3.0. Su cierre es obligatorio dentro del Sprint 2 y no puede prorrogarse otra vez sin una nueva enmienda. Mientras siga abierta, la constitución no da por terminado el Sprint 2 |

### Desviaciones aprobadas y ampliaciones

| Id | Qué | Estado |
|---|---|---|
| DV-07 | k6 en lugar de Locust para EQ-04, EQ-09 y el estrés (el enunciado pide k6); se conservan las medidas de `docs/` | Aprobada (v1.1.0) |
| DV-08 | Jest en el frontend y Postman/Newman para la API, que `docs/` no define | Ampliación aprobada (v1.1.0) |
| DV-10 | `almacen_documentos_disco.py` vive en `signing`, como indica el C4 nivel 3, y no en `requests` | Resuelta a favor del C4 (v1.3.0) |
| DV-01, DV-02 | El nivel del COLOGE (RN03) bloquea el envío en lugar de firmarse, y la aprobación automática (RN04) no se implementó | Pospuestas: fuera del alcance de 001 y 002 |
| DV-05, DV-06 | Alembic para las migraciones; el código vive en `tecnologia/` | Aprobadas en el plan de 001 |

### Pendientes del Sprint 2

- **HTTPS y despliegue** (cierre de DT-02).
- **EQ-05**: medir con Lighthouse. **EQ-06**: Uptime Kuma y `docker kill`.
- **Nivel del COLOGE** y aprobación automática (DV-01, DV-02).
- Repetir la prueba de estrés completa, sin interrupción, y aplicar el índice propuesto para la
  bandeja.
- Ejecutar con Newman la carpeta nueva de la colección de Postman (002), que ya está versionada
  (T042).

---

## 6. Criterio fundamental

> "Se evaluará que la implementación respete las decisiones arquitectónicas documentadas y que los
> estudiantes puedan demostrar, mediante pruebas, si la solución responde a los atributos de calidad
> establecidos."

**Respeto de las decisiones arquitectónicas.**

- `docs/` es de solo lectura. Toda diferencia con `docs/` se registra en la constitución con su
  motivo y su alcance; nunca se resuelve en silencio (principio I).
- Las decisiones se comprueban con pruebas, no solo con revisión: la prueba de reglas de
  dependencia hace cumplir ADR-001 (módulos) y ADR-002 (capas); la máquina de estados, ADR-007;
  la Unidad de Trabajo y el bloqueo de filas, ADR-003; la firma Ed25519 sobre SHA-256 y el PDF
  inmutable, ADR-004 y ADR-010; y el stack de ADR-011 se mantuvo, aunque eso exigió explicar el
  uso de Jest (sección 4).
- Cada plan tiene una revisión de la constitución ("Constitution Check") y cada desviación tiene su
  fila en "Complexity Tracking".

**Demostración mediante pruebas.**

- Cada escenario EQ-01 a EQ-09 tiene una prueba con la herramienta y la métrica de `docs/`, salvo
  dos sustituciones aprobadas (k6 y Jest); los resultados, con el dato obtenido y si cumple, están
  en [`evidencias/`](../evidencias/README.md).
- 7 de los 9 escenarios cumplen su métrica. EQ-05 y EQ-06 quedan como pendientes declarados, sin
  darlos por cumplidos.
- El pipeline de GitHub Actions repite las pruebas en cada cambio, y un pipeline en rojo bloquea la
  integración.
