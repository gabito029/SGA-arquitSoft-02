# Implementation Plan: Flujo principal de abastecimiento (incremento 001)

**Branch**: `001-flujo-solicitud` | **Date**: 2026-11-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-flujo-solicitud/spec.md`

## Summary

Implementar de punta a punta el flujo principal del SGA: el oficial de logística registra y envía
una solicitud; el comandante de la unidad, el jefe de logística de la División/Brigada y el jefe de
almacén la firman digitalmente por el conducto regular. Luego el almacenero la despacha descontando
el stock en una sola transacción con bloqueo, y el oficial firma el acta de recepción, que queda
inmutable y verificable.

La implementación sigue `docs/` al pie de la letra: monolito modular con Clean Architecture en
cada módulo, Python + FastAPI, PostgreSQL, React + TypeScript, Nginx y Docker Compose. La firma usa
SHA-256 + Ed25519, la trazabilidad se guarda en historial y auditoría encadenada, y las pruebas
usan pytest. Las solicitudes que requieren al COLOGE se bloquean al enviarlas hasta el
incremento 002. Las decisiones están justificadas en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend) · TypeScript 5 sobre Node.js 20 LTS, solo para
compilar el frontend

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, psycopg 3,
`cryptography` (Ed25519), PyJWT, bcrypt · React 18, React Router, Vite

**Storage**: PostgreSQL 16. Caché en memoria del proceso solo para el catálogo, con TTL de 300 s
(research §7). Los PDF en disco llegan en el incremento 002.

**Testing**: backend con pytest, pytest + httpx (`TestClient`) contra PostgreSQL real, pytest-cov
y Ruff. Frontend con **Jest** + React Testing Library (jsdom), con reporte de cobertura, más ESLint
y `tsc`. API con una colección **Postman**, que se ejecuta con Newman. Carga con **k6** (carga
progresiva hasta 2 000 usuarios virtuales). Usabilidad con Lighthouse. Research §9 y §11.

**Target Platform**: contenedores Linux con Docker Compose; navegador de escritorio y de celular

**Project Type**: aplicación web (API REST + SPA), con backend y frontend separados

**Performance Goals**: p95 < 2 s con 20 usuarios (EQ-04) y con 40 usuarios en 2 instancias
(EQ-09). Se miden en 002.

**Constraints**: API sin estado (JWT); toda operación que firma o cambia el stock en una sola
transacción (ADR-003); stock ≥ 0; registros firmados inmutables; solo herramientas gratuitas
(RC07); demo funcionando en **4 días** por una sola persona.

**Scale/Scope**: datos ficticios con 2 Grandes Unidades, 4 unidades, 2 almacenes, 14 ítems y
unos 12 usuarios; 5 pantallas; 19 operaciones REST; 7 de los 8 módulos (Reportes queda fuera)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Fidelidad a `docs/` (NO NEGOCIABLE) | Stack, estilo, enfoque, módulos y ADR de `docs/`; `docs/` no se modifica; artefactos en `specs/001-flujo-solicitud/` | ✅ |
| II. Especificaciones SDD | `spec.md` aprobado con criterios Dado/Cuando/Entonces | ✅ |
| III. Desarrollo incremental | Flujo completo en 001 con la secuencia de 4 días; lo demás va a 002 (ver abajo) | ✅ |
| IV. API REST documentada | `contracts/openapi.yaml`; FastAPI expone `/docs` y `/openapi.json`; `/health` | ✅ |
| V. Diseño limpio | Patrones de `docs/` más Strategy en las reglas y la firma, justificados abajo | ✅ |
| VI. Pruebas con pytest (NO NEGOCIABLE) | Backend: unitarias de dominio, integración con PostgreSQL, cobertura ≥ 60 % en módulos críticos y Ruff. Frontend: Jest con cobertura (agregado; no contradice VI, que regula el backend). Todo en GitHub Actions en push y PR | ✅ |
| VII. Atributos de calidad | EQ-01, 02, 03, 07 (parcial) y 08 (adaptado) en 001; EQ-04, 05, 06, 09 y estrés en 002; evidencias en `evidencias/`. La herramienta de carga es k6 en lugar de Locust; las medidas de `docs/` no cambian | ✅ con desviaciones declaradas (DV-03, DV-07) |
| VIII. Datos y caché | Índices, paginación, transacciones con bloqueo, migraciones Alembic, seeds; caché sin contenedor nuevo | ✅ |
| IX. Reglas de dominio | Máquina de estados de `docs/`, firma Ed25519 por nivel y acta, auditoría encadenada, nada se borra | ✅ con desviaciones temporales (DV-01, DV-02) |
| X. Actores y seguridad | JWT, rol y órgano en cada petición; 401/403/404; bcrypt; secretos en `.env` | ✅ (HTTPS en 002, DV-04) |
| XI. Español y Conventional Commits | Código, comentarios y documentación en español sin tildes en los nombres | ✅ |

**Conflictos reportados (principio I)**:

1. **Backend**: el primer pedido del plan indicaba Node.js + Jest + Supertest. Se resolvió a favor
   de `docs/` (ADR-011): Python + FastAPI con pytest + httpx, por decisión de la autora del
   2026-11-22.
2. **Herramienta de carga**: EQ-04 y EQ-09 de `docs/` nombran Locust. Por decisión de la autora
   (2026-11-22) se usa **k6**, porque el entregable del Sprint 2 exige explícitamente k6 con carga
   progresiva hasta 2 000 usuarios virtuales y k6 no depende del lenguaje del backend. Se cambia
   solo la herramienta; el estímulo y las medidas de EQ-04 y EQ-09 se mantienen como criterio de
   aceptación. Queda registrado como DV-07.
3. **Jest en el frontend y Postman**: `docs/` no define pruebas del frontend ni una colección de
   API, así que son **ampliaciones**, no contradicciones. Cubren el requisito del entregable de
   "pruebas automatizadas con Jest y reporte de cobertura".

> **Seguimiento de la constitución**: la tabla de conflictos de la constitución v1.0.0 dice
> "Locust; la prueba de 2 000 usuarios es estrés adicional", y el principio VII nombra Locust para
> EQ-04 y EQ-09. Esta decisión de la autora la sustituye por k6. Se recomienda enmendarla con
> `/speckit-constitution` (PATCH a v1.0.1: cambio de herramienta, sin cambio de significado) para
> que la constitución y el plan no queden desalineados. Hasta entonces, DV-07 deja el cambio
> justificado y visible.

**Resultado del gate**: aprobado. Las desviaciones están en Complexity Tracking.
**Re-evaluación tras la Fase 1 y los ajustes**: aprobado. Jest, Postman/Newman y k6 son
herramientas de prueba que no se despliegan, así que no agregan contenedores ni componentes al
C4. El modelo de datos y el contrato no cambian.

## Arquitectura aplicada

### Módulos del monolito en 001 (C4 nivel 3)

| Módulo | Qué entra en 001 | Fuera de 001 |
|---|---|---|
| `identity` | Inicio de sesión, JWT, `usuario_actual`, guardas por rol | Gestión de usuarios (HU11) |
| `catalog` | Lectura de órganos, almacenes e ítems, con caché | Altas, bajas y cambios (HU11) |
| `requests` | Registrar, editar, enviar, anular, firmar o rechazar, línea de tiempo, bandejas | — (módulo núcleo) |
| `rules` | `ReglaAprobacion`: exige COLOGE por material de guerra o monto alto | Aprobación automática (RN04) |
| `signing` | Huella SHA-256, firma Ed25519, verificación | PDF y `AlmacenDocumentos` (ADR-010) |
| `inventory` | Stock, movimientos, despacho con bloqueo | Salidas propias (HU09), alertas (HU10) |
| `audit` | Registro encadenado dentro de cada transacción | Verificación de la cadena por el auditor (HU12) |
| `reports` | — | Panel de control (HU13) |

`requests` coordina a `rules`, `signing`, `inventory` y `audit` solo a través de sus servicios
públicos, nunca de sus tablas. Todos comparten la misma Unidad de Trabajo para que la operación
sea una sola transacción.

### SOLID y patrones (principio V)

| Patrón / principio | Dónde | Justificación |
|---|---|---|
| **State** (ADR-007) | `requests/dominio/requerimiento.py` + `estado.py` | La entidad decide qué transición es válida y lanza `TransicionNoPermitida`; así ningún nivel se omite (RN01, RN02) |
| **Repository** + **Inversión de dependencias** | `dominio/puertos.py` → `infraestructura/repositorio_postgres.py` | Los casos de uso no conocen SQLAlchemy, y el dominio se prueba sin base de datos |
| **Unit of Work** (ADR-003) | `core/unidad_trabajo.py` | Estado, firma, movimientos, historial y auditoría se guardan juntos o no se guarda nada |
| **Adapter / Strategy** para la firma | Puerto `FirmadorDocumentos` → `FirmadorEd25519` (y `FirmadorFalso` en pruebas) | Cambiar a certificados acreditados (RC01) es un adaptador nuevo. Cada firma guarda su `metodo` para elegir la estrategia de verificación (Liskov, Abierto/cerrado) |
| **Strategy** para las reglas | `rules/dominio/regla_aprobacion.py` (`ReglaCologePorCategoriaOMonto`) | En 002 se agrega `ReglaAprobacionAutomatica` sin tocar `requests`, que es lo que mide EQ-07 |
| **Inyección de dependencias** | `main.py` + `dependencias.py` con `Depends` de FastAPI | La raíz de composición decide los adaptadores, y las pruebas los sustituyen |
| **Segregación de interfaces** | Puertos pequeños: repositorio, firmador, auditoría y servicio de inventario | Ningún adaptador implementa métodos que no usa |
| **Factory** | No se usa en 001 | No hace falta: un solo adaptador por puerto. Se justificará si aparece una familia de objetos |

## Project Structure

### Documentation (this feature)

```text
specs/001-flujo-solicitud/
├── spec.md
├── plan.md              # este archivo
├── research.md          # decisiones técnicas (Fase 0)
├── data-model.md        # entidades, estados, índices y seeds (Fase 1)
├── quickstart.md        # levantar y validar el flujo (Fase 1)
├── contracts/
│   └── openapi.yaml     # contrato REST (Fase 1)
├── checklists/
│   └── requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

El código va en `tecnologia/`, como indica el README. Dentro se respeta literalmente la
estructura del diseño interno de `docs/` (`backend/app/modules/<modulo>/{dominio,aplicacion,
infraestructura,presentacion}`).

```text
.github/workflows/
└── ci.yml                         # lint + pruebas en cada push y pull request

tecnologia/
├── docker-compose.yml             # db, api (restart: always), web (Nginx)
├── .env.example                   # variables sin valores secretos
├── nginx/
│   └── default.conf               # sirve el frontend y reenvía /api, /docs y /health a la API
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml             # dependencias, configuración de Ruff, pytest y coverage
│   ├── alembic.ini
│   ├── migrations/                # migraciones versionadas (tablas, índices, disparadores)
│   ├── seeds/
│   │   └── cargar.py              # datos ficticios idempotentes
│   ├── scripts/
│   │   └── generar_clave_firma.py
│   ├── app/
│   │   ├── main.py                # raíz de composición: crea la app y registra los módulos
│   │   ├── core/                  # configuración, base de datos, unidad de trabajo, JWT, errores, /health
│   │   └── modules/
│   │       ├── identity/          # dominio · aplicacion · infraestructura · presentacion
│   │       ├── catalog/
│   │       ├── requests/          # núcleo, con la estructura completa del diseño interno de docs/
│   │       │   ├── dominio/        requerimiento.py, estado.py, firma_nivel.py, puertos.py, errores.py
│   │       │   ├── aplicacion/     registrar_requerimiento.py, enviar_requerimiento.py,
│   │       │   │                   firmar_requerimiento.py, anular_requerimiento.py,
│   │       │   │                   despachar_requerimiento.py, confirmar_recepcion.py,
│   │       │   │                   consultar_requerimientos.py
│   │       │   ├── infraestructura/ modelos.py, repositorio_postgres.py, dependencias.py
│   │       │   └── presentacion/   router.py, esquemas.py
│   │       ├── rules/             # dominio/regla_aprobacion.py
│   │       ├── signing/           # dominio/puertos.py, contenido_canonico.py; infraestructura/firmador_ed25519.py
│   │       ├── inventory/         # stock, movimientos, servicio de despacho con bloqueo
│   │       └── audit/             # registro encadenado
│   └── tests/
│       ├── unitarias/             # dominio puro: estados, reglas, contenido canónico, firma
│       └── integracion/           # API + PostgreSQL: test_eq01…, test_eq02…, test_eq03…, test_eq08…
├── frontend/
│   ├── Dockerfile                 # build con Vite → imagen de Nginx
│   ├── package.json               # scripts: dev, build, lint, test, test:cov
│   ├── vite.config.ts
│   ├── jest.config.ts             # ts-jest + jsdom, umbral de cobertura
│   ├── src/
│   │   ├── config.ts              # única lectura de import.meta.env (se sustituye en Jest)
│   │   ├── api/                   # cliente fetch con JWT, tipos tomados de openapi.yaml
│   │   ├── auth/                  # contexto de sesión y rutas protegidas por rol
│   │   ├── logica/                # validaciones del formulario, acciones por rol, etiquetas de estado
│   │   ├── componentes/           # Formulario, Tabla, LineaTiempo, Estado, Mensaje, Cargando
│   │   └── paginas/               # InicioSesion, Bandeja, NuevaSolicitud, DetalleSolicitud, Stock
│   └── tests/                     # *.test.ts(x) con Jest + React Testing Library
└── pruebas/
    ├── postman/
    │   ├── sga-001.postman_collection.json   # flujo completo + casos 401/403/404/409
    │   └── local.postman_environment.json
    └── k6/
        ├── eq04_rendimiento.js    # 20 VU durante 5 min (60/30/10)
        ├── eq09_escalabilidad.js  # 40 VU con 1 y 2 instancias
        └── estres_2000.js         # rampa progresiva hasta 2 000 VU

evidencias/                         # fuera de docs/ (principio VII)
└── EQ-01 … EQ-09/                  # reportes de pytest, Jest, Newman, k6 y Lighthouse
```

**Structure Decision**: aplicación web con backend y frontend separados, dentro de `tecnologia/`.
El backend reproduce la estructura de módulos y capas del diseño interno y del C4 nivel 3 de
`docs/`. Los nombres de los módulos (`requests`, `identity`, …) se toman literalmente del C4 nivel
3; las capas internas van en español.

## Estrategia de pruebas (principios VI y VII)

### Pirámide

| Nivel | Herramienta | Qué cubre |
|---|---|---|
| Unitarias | pytest | Todas las transiciones válidas e inválidas de `Requerimiento`, `ReglaAprobacion` (categoría y umbral), contenido canónico estable, firma y verificación Ed25519 (incluido un byte alterado), validaciones de cantidades |
| Integración | pytest + httpx `TestClient` + PostgreSQL | Cada endpoint del contrato: códigos 401/403/404/409/422, transacciones, disparadores de inmutabilidad, historial y auditoría |
| Calidad | Ruff; pytest-cov con `--cov-fail-under=60` en `requests`, `rules`, `signing` e `inventory` | EQ-07 |
| Frontend | **Jest** + React Testing Library (jsdom), cobertura con umbral del 60 % en `src/logica`, `src/auth` y `src/api` | Validaciones del formulario (≥ 1 ítem, cantidad > 0, sin repetidos, una categoría); acciones visibles por rol y estado; rutas protegidas; manejo de 401 (cierra la sesión), 403/404/409/422 (mensajes en español) y estados de carga; inicio de sesión y nueva solicitud con la API simulada |
| E2E de API | pytest; colección **Postman** ejecutada con Newman | Flujo completo (EQ-08 adaptado). La colección también sirve de demo de respaldo y de evidencia de EQ-01 |
| Carga | **k6** | EQ-04, EQ-09 y estrés hasta 2 000 VU (002) |
| Usabilidad / disponibilidad | Lighthouse, `docker kill` + Uptime Kuma | En 002 |

### Escenarios de calidad de `docs/`

| Escenario | Prueba | Incremento |
|---|---|---|
| EQ-01 Seguridad | `test_eq01_control_acceso.py`: cada rol intenta firmar, aprobar, despachar y firmar el acta sin que le corresponda, y lee solicitudes de otra unidad; se espera 401, 403 o 404 en el 100 % de los casos | **001** |
| EQ-02 Integridad | Unitaria: se altera un byte del contenido firmado y la firma Ed25519 falla. Integración: se desactiva el disparador, se cambia una cantidad firmada y `/verificacion` responde `ALTERADA` | **001** |
| EQ-03 Consistencia | `test_eq03_concurrencia.py`: dos hilos despachan 7 + 7 unidades con stock 10; se espera un éxito y un 409, stock final 3, y la consulta SQL de stock contra Σ movimientos da 0 diferencias | **001** |
| EQ-07 Mantenibilidad | Cobertura ≥ 60 % y 0 errores de Ruff en CI. La prueba de cambiar el umbral del COLOGE con `git diff --stat` solo en `rules` | Parcial en **001** (cobertura y Ruff); el cambio de regla en **002** |
| EQ-08 Trazabilidad | `test_eq08_trazabilidad.py`: flujo completo con 5 pasos firmados (sin COLOGE) más el envío; la consulta SQL confirma usuario, órgano y fecha en cada paso | **001**, adaptado; con los 6 pasos y el COLOGE en **002** |
| EQ-04 Rendimiento | k6 `eq04_rendimiento.js`: 20 VU durante 5 min (60 % lista, 30 % detalle, 10 % registro), con umbrales `p(95)<2000` y `http_req_failed<1%`, con y sin la caché del catálogo | Script y una corrida de referencia en **001** si sobra tiempo el día 4; validación formal en **002** |
| EQ-05 Usabilidad | Lighthouse en modo celular sobre inicio de sesión, registro y bandeja (≥ 80), contando los campos del formulario | **002** (el formulario de 001 ya respeta 5 campos como máximo) |
| EQ-06 Disponibilidad | `docker kill` de la API 3 veces; Uptime Kuma sobre `/health` cada 20 s; se espera recuperación en menos de 1 min | **002** (`restart: always` y `/health` ya están en 001) |
| EQ-09 Escalabilidad | k6 `eq09_escalabilidad.js`: 40 VU con 1 y con 2 instancias (`--scale api=2`) detrás de Nginx; se comparan los p95 | **002** |
| Estrés (entregable del Sprint 2) | k6 `estres_2000.js`: rampa progresiva (`ramping-vus`) de 0 a 2 000 VU por escalones (50 → 200 → 500 → 1 000 → 2 000), registrando p95, tasa de errores y punto de quiebre. Se ejecuta desde la máquina local contra Docker Compose, no en CI | **002** |

Las evidencias de cada escenario se guardan en `evidencias/EQ-0X/`: salida de pytest, `htmlcov/`,
cobertura de Jest (`coverage/lcov-report`), reporte de Newman, resumen de k6 (`--summary-export`
en JSON), JSON de Lighthouse y capturas.

## CI (GitHub Actions) y entorno local

- **`.github/workflows/ci.yml`**, que se dispara con `push` y `pull_request` en todas las ramas:
  - **backend**: Python 3.12 con el servicio `postgres:16`. Ejecuta `pip install -e .[dev]`,
    `ruff check`, `ruff format --check`, `alembic upgrade head` y
    `pytest --cov --cov-fail-under=60`, y sube `coverage.xml` y `htmlcov/` como artefacto.
  - **frontend**: Node 20. Ejecuta `npm ci`, `npm run lint`, `tsc --noEmit`,
    `npm run test:cov` (Jest con `--coverage` y umbral del 60 %; falla si no se alcanza) y
    `npm run build`, y sube `coverage/` como artefacto.
  - Las pruebas de carga con k6 y la colección de Postman no corren en CI. Un runner gratuito no
    soporta 2 000 VU, y Newman necesita el sistema levantado. Se ejecutan en local y sus reportes
    van a `evidencias/`.
- **Docker Compose** (`tecnologia/docker-compose.yml`):
  - `db` (postgres:16 con volumen y healthcheck).
  - `api` (FastAPI con uvicorn, `restart: always` y healthcheck sobre `/health`, ADR-013).
  - `web` (Nginx con el build del frontend y proxy a `api`, ADR-012).
  - En 002 se suman `uptime-kuma` y el escalamiento `--scale api=2`.

## Plan de 4 días (demo)

El frontend avanza **en paralelo desde el día 2**. Cada día termina con algo demostrable de punta
a punta. La regla es hacer primero el backend de cada funcionalidad y por la tarde su pantalla,
contra la API real.

| Día | Backend | Frontend | Demostrable al final del día |
|---|---|---|---|
| **1** | Estructura de `tecnologia/`, Docker Compose, migraciones (tablas, índices, disparadores), seeds, inicio de sesión con JWT, catálogo con caché, `/health` y `/docs`. Dominio de `Requerimiento` y `ReglaAprobacion` con pruebas unitarias | Proyecto Vite + TS, ESLint, **Jest configurado** con una primera prueba y `src/config.ts`. CI en verde con los dos trabajos | Inicio de sesión por Swagger |
| **2** | Registrar, editar, enviar (con bloqueo del COLOGE), anular, firmar o rechazar los 3 niveles con Ed25519, historial y auditoría encadenada. Pruebas de integración de EQ-01 | **Inicio de sesión**, sesión y rutas por rol, cliente de API, **Nueva solicitud** con validación (5 campos como máximo), mensajes y carga. Pruebas Jest de validaciones, acciones por rol y manejo de errores | Registrar y enviar desde la web; firmar por Swagger |
| **3** | Despacho con bloqueo de stock, acta de recepción, verificación, bandejas paginadas y stock. Pruebas de EQ-02, EQ-03 y EQ-08; cobertura ≥ 60 % | **Bandeja** por rol y **Detalle** con línea de tiempo y botones Firmar/Rechazar (con motivo). Pruebas Jest de los componentes | Todo el conducto regular desde la web |
| **4** | Correcciones; colección **Postman** del flujo; script k6 de EQ-04 y una corrida de referencia si sobra tiempo | **Despachar**, **Firmar acta**, **Verificar** y **Stock**; ajuste responsive; cobertura Jest ≥ 60 % | Flujo completo desde la web; ensayo del quickstart; evidencias en `evidencias/` |

**Demo de respaldo**: si alguna pantalla no está lista, ese paso se muestra desde Swagger
(`/docs`), que tiene todos los endpoints, o con la colección de Postman, iniciando sesión con cada
usuario de prueba. Como el backend completo está listo el día 3, la demo del flujo nunca depende
del frontend.

**Si falta tiempo**, se recorta en este orden: la pantalla de stock (se consulta por Swagger), la
edición de un borrador (se crea uno nuevo), el filtro por estado en la bandeja y la corrida de k6
del día 4 (pasa a 002).

## Pendiente para el incremento 002

- Nivel del COLOGE (HU04, RN03 completa) y aprobación automática (RN04, HU06).
- PDF de cada firma y del acta (RF05, ADR-010, ReportLab).
- Verificación de la auditoría encadenada por el auditor (HU12, RF11).
- EQ-04, EQ-05, EQ-06 y EQ-09, más la prueba de estrés de 2 000 usuarios; Uptime Kuma; escalamiento
  con Nginx; la prueba de EQ-07 sobre el cambio de regla; EQ-08 con los 6 pasos.
- HTTPS (AC01) con certificado local o de un servicio gratuito, y evaluar Redis solo si EQ-04 lo
  justifica.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| DV-01: las solicitudes que requieren al COLOGE se bloquean al enviarlas (RN03 sin el nivel del COLOGE) | El nivel del COLOGE no entra en la demo de 4 días; la spec (FR-012) y la constitución lo piden así | Permitir el envío saltando al COLOGE rompería RN02; incluir el COLOGE pone en riesgo el plazo |
| DV-02: la aprobación automática (RN04) se pospone y todas las solicitudes pasan por el jefe de almacén | Simplifica el MVP; agrega un control, no lo quita | Implementarla ahora suma reglas y pruebas sin aportar a la demo |
| DV-03: EQ-04, 05, 06 y 09 se validan en 002, y EQ-07 y EQ-08 de forma parcial | Una persona en 4 días; primero se prueba la lógica crítica (principio VI) | Correr carga y Lighthouse sin el flujo terminado no valida nada |
| DV-04: HTTPS (AC01) en 002; en local se usa HTTP | El entorno local de la demo no expone el sistema | Certificados en el día 1 consumen tiempo sin cambiar la lógica |
| DV-05: Alembic como herramienta de migraciones, que `docs/` no nombra | La constitución (VIII) exige migraciones versionadas; Alembic pertenece al ecosistema SQLAlchemy que fija `docs/` | Crear el esquema con `create_all` impide versionar cambios |
| DV-06: el código va en `tecnologia/` en lugar de la raíz `backend/` del diseño interno | Lo indica el README; la estructura interna se mantiene idéntica | Mover `backend/` a la raíz contradiría el README sin aportar nada |
| DV-07: **k6** en lugar de Locust para EQ-04, EQ-09 y el estrés de 2 000 VU (EQ-04 y EQ-09 de `docs/` nombran Locust) | Lo exige explícitamente el entregable del Sprint 2; k6 no depende del lenguaje del backend; tiene rampas `ramping-vus` y umbrales `p(95)` declarativos que coinciden con las medidas de `docs/`. Decisión de la autora del 2026-11-22 | Locust cumple las medidas de `docs/`, pero no el requisito explícito del entregable; usar ambos duplica scripts sin aportar nada. Las medidas de `docs/` no cambian, solo la herramienta |
| DV-08: **Jest** en el frontend y **Postman/Newman** para la API (`docs/` no los define) | El entregable exige "pruebas automatizadas con Jest y reporte de cobertura"; Postman da una colección del flujo que sirve de prueba de API y de respaldo para la demo | Dejar el frontend sin pruebas no cumple el entregable; usar Jest en el backend contradice ADR-011. Son herramientas de prueba que no agregan componentes al C4 |
