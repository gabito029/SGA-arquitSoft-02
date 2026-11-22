# Research: Incremento 001 — Flujo principal de abastecimiento

**Fecha**: 2026-11-22 · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Cada decisión parte de `docs/` (fuente de verdad, constitución principio I). Cuando `docs/` no
decide algo, se elige lo más simple que una sola persona pueda construir en 4 días.

## 1. Lenguaje y framework del backend

- **Decision**: Python 3.12 + FastAPI.
- **Rationale**: lo fijan ADR-011, C4 niveles 2–4, el diseño interno y la constitución
  (principio I, NO NEGOCIABLE). La autora confirmó el 2026-11-22 seguir `docs/` ("solo era una
  sugerencia Jest"). FastAPI genera OpenAPI/Swagger en `/docs` sin trabajo extra (principio IV).
- **Alternatives considered**: Node.js + TypeScript + Jest (pedido del prompt de plan). Rechazado:
  contradice ADR-011 y la constitución; exigiría enmienda MAJOR de la constitución y un cambio
  manual de ADR-011 y del C4 por parte de la autora.

## 2. Persistencia, migraciones y seeds

- **Decision**: PostgreSQL 16, SQLAlchemy 2.0 (ORM, estilo síncrono), **Alembic** para
  migraciones y un script de seeds idempotente (`python -m seeds.cargar`) versionado en Git.
- **Rationale**: PostgreSQL y SQLAlchemy los fija `docs/`. Alembic es la herramienta de
  migraciones del propio proyecto SQLAlchemy: no agrega un componente nuevo y cumple el principio
  VIII. Síncrono porque las transacciones con bloqueo (ADR-003) son más simples de razonar y
  probar; con 20–40 usuarios (EQ-04/EQ-09) no hace falta asincronía.
- **Alternatives considered**: SQLAlchemy asíncrono (más complejo, sin beneficio medible a esta
  escala); SQL a mano (rompe Repository y duplica esfuerzo).

## 3. Firma digital

- **Decision**: huella SHA-256 sobre la **representación canónica** del contenido firmado (JSON
  con claves ordenadas, sin espacios, UTF-8), firmada con **Ed25519** usando la clave del sistema
  (ADR-004) mediante la librería `cryptography`. Cada firma guarda `metodo = "ed25519-sha256-v1"`,
  el identificador de la clave, la huella y la firma en base64.
- **Rationale**: es el mecanismo de `docs/`; guardar el método permite cambiar a certificados
  acreditados (RC01) sin invalidar firmas viejas. La clave privada llega por variable de entorno
  (principio X); en local se genera con un script.
- **Contenido firmado**: para cada nivel, el identificador y los ítems de la solicitud, el nivel,
  la decisión, el firmante (id, rol, órgano) y la fecha y hora. Para el acta, además lo
  despachado, lo recibido y las observaciones.
- **Verificación**: se recalcula la huella con los datos **actuales** de la base de datos y se
  comprueba la firma; si cualquiera de las dos falla, el resultado es ALTERADA (EQ-02).
- **PDF (RF05)**: se pospone al incremento 002 (ReportLab + `AlmacenDocumentos` en disco,
  ADR-010), como permite la constitución.
- **Alternatives considered**: solo SHA-256 sin firma (contradice ADR-004); HMAC (no es firma
  asimétrica y no permite verificar con clave pública).

## 4. Autenticación y autorización

- **Decision**: inicio de sesión con usuario y contraseña; contraseñas con hash **bcrypt**; token
  **JWT HS256** de 60 minutos con `sub`, `rol` y `organo_id` (ADR-006). Dependencias de FastAPI
  validan el token y el rol; la regla de jurisdicción (unidad, Gran Unidad, almacén) se aplica en
  la capa de aplicación al cargar la solicitud. Un recurso ajeno responde **404** (EQ-01).
- **Rationale**: sin estado en el servidor, lo que permite varias instancias (ADR-012).
- **Alternatives considered**: sesiones en servidor (rompe ADR-006); token de refresco (no hace
  falta para la demo; 002 si se necesita).

## 5. Concurrencia y consistencia del inventario

- **Decision**: cada caso de uso que cambia estado abre **una transacción** (Unit of Work) y
  bloquea la fila de la solicitud con `SELECT … FOR UPDATE`. El despacho bloquea además las filas
  de stock afectadas, **ordenadas por `item_id`** para evitar interbloqueos, valida el stock y
  registra los movimientos. Restricción `CHECK (cantidad >= 0)` en stock como segunda barrera.
  Restricción única `(requerimiento_id, nivel)` en firmas: un nivel firma una sola vez (RN02).
- **Rationale**: ADR-003 y EQ-03; si dos almaceneros despachan a la vez, el segundo espera, ve el
  stock real y es rechazado con 409.
- **Alternatives considered**: bloqueo optimista con versión (más reintentos en el cliente);
  nivel de aislamiento SERIALIZABLE (más fallos de serialización a manejar).

## 6. Trazabilidad y auditoría encadenada

- **Decision**: una tabla `historial_requerimiento` (línea de tiempo de la spec) y una tabla
  `registro_auditoria` **encadenada** (ADR-005): cada registro guarda la huella del anterior. Ambas
  se escriben en la misma transacción que el cambio (RN07). Para encadenar sin carreras se toma un
  `pg_advisory_xact_lock` fijo antes de leer el último registro.
- **Inmutabilidad**: un disparador en la base de datos rechaza `UPDATE` y `DELETE` sobre
  `firma`, `acta_recepcion`, `movimiento`, `historial_requerimiento` y `registro_auditoria`.
- **En 001**: se registra la cadena. **En 002**: el endpoint del auditor que verifica la cadena
  completa (HU12/RF11).
- **Alternatives considered**: solo historial sin cadena (incumple ADR-005 y el principio IX).

## 7. Caché

- **Decision**: `docs/` no define una caché, y no se agrega ningún contenedor nuevo.
  - **Se cachea**: el catálogo de ítems y la estructura orgánica, que en 001 solo cambian con
    los seeds. Se guardan en memoria del proceso con TTL de **300 s**, y el `GET /catalogo/items`
    lleva la cabecera `Cache-Control: max-age=300`. Nginx sirve los archivos estáticos del
    frontend con huella en el nombre y `Cache-Control: max-age=31536000, immutable`.
  - **No se cachea**: solicitudes, stock, firmas e historial, porque la consistencia (AC03)
    prima sobre la velocidad.
  - **Invalidación**: por TTL, y además al reiniciar el proceso, que es lo que pasa cuando se
    recargan los seeds. Cuando llegue la gestión del catálogo (HU11, otro incremento), cada
    escritura del catálogo borrará la entrada correspondiente.
  - **Medición**: en 002, EQ-04 se corre con y sin la caché del catálogo y se comparan los p95.
- **Rationale**: con 20–40 usuarios el cuello de botella no es el catálogo. Una caché en memoria
  de datos que casi no cambian es segura aunque haya varias instancias: como mucho, cada una
  queda desactualizada durante el TTL.
- **Alternatives considered**: Redis. Sería un contenedor fuera del nivel 2 del C4 y, según el
  principio VIII, una desviación que hay que reportar. Solo se propondrá si las pruebas de
  k6 de 002 lo justifican (§11).

## 8. Frontend

- **Decision**: React 18 + TypeScript + Vite, React Router y `fetch` con un cliente mínimo que
  agrega el JWT. Sin librería de componentes: CSS propio responsive. ESLint + `tsc` como lint.
  Las pruebas usan Jest (§12).
- **Rationale**: React + TS lo fija `docs/`; Vite es la forma estándar y más rápida de crear el
  proyecto. Son pocas pantallas (5) para la demo.
- **Alternatives considered**: librería de componentes (más dependencias sin necesidad).

## 9. Pruebas y herramientas por escenario

- **Decision**: en el **backend**, las herramientas que fija `docs/`: pytest (unitarias),
  pytest + httpx `TestClient` (integración contra PostgreSQL real), pytest-cov (cobertura) y Ruff
  (lint y formato). Para los escenarios: Lighthouse (EQ-05) y `docker kill` + Uptime Kuma
  (EQ-06), como dice `docs/`; **k6** para la carga (EQ-04, EQ-09 y estrés, §11) y **Postman**
  para la API (§13). En el **frontend**, Jest (§12).
- **Rationale**: constitución principios VI y VII. En el backend no se usan Jest ni Supertest,
  porque contradicen ADR-011.
- **Alternatives considered**: base de datos SQLite en las pruebas (no reproduce `FOR UPDATE` ni
  los disparadores; EQ-03 exige PostgreSQL).

## 10. CI y entorno local

- **Decision**: GitHub Actions con dos trabajos. El del **backend** corre `ruff check`,
  `ruff format --check`, `alembic upgrade head` y `pytest --cov`, con PostgreSQL 16 como servicio;
  el umbral es `--cov-fail-under=60` sobre los módulos críticos y el reporte se sube como
  artefacto. El del **frontend** corre `npm ci`, `eslint`, `tsc --noEmit`, `jest --coverage` (falla si la
  cobertura baja del umbral, §12) y `vite build`. Se
  ejecuta en cada push y pull request. Docker Compose levanta `db`, `api` (`restart: always`,
  ADR-013) y `web`: Nginx sirve el build del frontend y reenvía `/api` a la API, como en el nivel 2
  del C4.
- **Rationale**: principio VI, RC08 y ADR-012/013.
- **Alternatives considered**: despliegue continuo (no lo exige la constitución vigente; se
  evalúa después).

## 11. Pruebas de carga con k6 (en lugar de Locust)

- **Decision**: **k6** para EQ-04, EQ-09 y la prueba de estrés del entregable del Sprint 2, con
  carga progresiva hasta **2 000 usuarios virtuales concurrentes**. Hay tres scripts en
  `tecnologia/pruebas/k6/`:
  - `eq04_rendimiento.js`: 20 VU constantes durante 5 min, con mezcla 60 % lista, 30 % detalle y
    10 % registro.
  - `eq09_escalabilidad.js`: 40 VU, contra 1 y contra 2 instancias.
  - `estres_2000.js`: ejecutor `ramping-vus` con escalones 50 → 200 → 500 → 1 000 → 2 000.

  Los criterios se escriben como `thresholds` (`http_req_duration: p(95)<2000`,
  `http_req_failed: rate<0.01`). Cada VU inicia sesión una vez en `setup()` y reutiliza el JWT.
  Los resultados se exportan con `--summary-export` a `evidencias/EQ-0X/`. Se ejecuta en local
  contra Docker Compose, no en CI.
- **Rationale**: es una decisión de la autora del 2026-11-22. El entregable del Sprint 2 exige k6
  explícitamente. k6 es independiente del lenguaje del backend, sus rampas y umbrales
  declarativos expresan directamente las medidas de `docs/` (p95 < 2 s) y es gratuito (RC07).
  **Se cambia solo la herramienta**: el estímulo, la mezcla de operaciones y las medidas de
  EQ-04 y EQ-09 siguen siendo los de `docs/` y son el criterio de aceptación. La corrida de 2 000
  VU se reporta como estrés y punto de quiebre.
- **Conflicto con `docs/`**: EQ-04 y EQ-09 nombran Locust. Queda reportado como DV-07 en el plan,
  y se recomienda una enmienda PATCH de la constitución, que hoy dice Locust.
- **Alternatives considered**:
  - Locust: cumple `docs/`, pero no el requisito explícito del entregable.
  - Locust y k6 a la vez: duplica scripts y evidencias.
  - Correr la carga en GitHub Actions: un runner gratuito no sostiene 2 000 VU, y los resultados
    no serían representativos.

## 12. Pruebas del frontend con Jest

- **Decision**: **Jest** con `ts-jest`, entorno `jsdom` y React Testing Library
  (`@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`), con
  reporte de cobertura `--coverage` (texto, lcov y html) y `coverageThreshold` global del 60 %
  sobre `src/logica`, `src/auth` y `src/api`. Se prueban:
  - Las validaciones del formulario.
  - Las acciones visibles por rol y estado.
  - Las rutas protegidas.
  - El manejo de errores 401, 403, 404, 409 y 422, con mensajes en español.
  - Los estados de carga.
  - Las pantallas de inicio de sesión y nueva solicitud, con `fetch` simulado.

  Se ejecuta en GitHub Actions (`npm run test:cov`), y la cobertura se sube como artefacto.
- **Rationale**: el entregable exige "pruebas automatizadas con Jest y reporte de cobertura".
  `docs/` no define pruebas del frontend, así que es una **ampliación** que no contradice ADR-011,
  y el backend sigue con pytest. Jest corre sobre Node, que el frontend ya necesita para compilar.
- **Detalle técnico**: Vite expone las variables con `import.meta.env`, que Jest (CommonJS) no
  entiende. Por eso toda lectura de entorno se concentra en `src/config.ts`, y Jest lo sustituye
  con `moduleNameMapper`. Los estilos se simulan con `identity-obj-proxy`.
- **Alternatives considered**:
  - Vitest: se integra mejor con Vite, pero no cumple el requisito literal de Jest.
  - Jest en el backend: contradice ADR-011.
  - Pruebas E2E en navegador (Playwright): más tiempo del que permite la demo; se evalúan
    después.

## 13. Pruebas de la API con Postman

- **Decision**: una colección **Postman** (`tecnologia/pruebas/postman/sga-001.postman_collection.json`)
  con un entorno local. Contiene:
  - Inicio de sesión de cada rol, guardando el token en variables.
  - El flujo completo: registrar, enviar, visto bueno, conformidad, aprobación, despacho, acta y
    verificación.
  - Los casos de EQ-01 (401, 403 y 404) y los conflictos 409 (nivel ya firmado, stock
    insuficiente, requiere COLOGE).

  Cada petición tiene `pm.test` con el código y los campos esperados. Se ejecuta con
  **Newman** (`npx newman run … -r cli,htmlextra`) contra Docker Compose, y el reporte va a
  `evidencias/`.
- **Rationale**: el entregable la pide. Sirve como prueba de la API desde fuera del proceso y
  como **demo de respaldo**, sin depender del frontend. Las pruebas de pytest siguen siendo la
  fuente de verdad de la lógica (principio VI).
- **Alternatives considered**: solo Swagger (no deja pruebas repetibles); Newman en CI (necesita
  levantar todo el sistema en el runner; se evalúa en 002).

