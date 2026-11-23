---

description: "Lista de tareas del incremento 001 — flujo principal de abastecimiento"
---

# Tasks: Flujo principal de abastecimiento (incremento 001)

**Input**: Documentos de diseño en `specs/001-flujo-solicitud/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/openapi.yaml](contracts/openapi.yaml),
[quickstart.md](quickstart.md)

**Tests**: obligatorias por la constitución v1.2.0 (principios VI y VII): pytest + httpx en el
backend, Jest en el frontend y k6 para la carga. Cada prueba está junto a la funcionalidad que
valida.

**Organization**: fases por historia de usuario en orden de prioridad. Cada fase indica su **día**
del plan de 4 días, y al final está el [calendario por día](#calendario-por-día).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo y sin dependencias pendientes)
- **[Story]**: historia de `spec.md` (US1 … US6)
- Las restricciones de los campos se citan como `data-model.md Entidad.campo`; la definición
  canónica está en [data-model.md](data-model.md)

## Path Conventions

- Backend: `tecnologia/backend/app/` (módulos en `app/modules/<modulo>/{dominio,aplicacion,infraestructura,presentacion}/`), pruebas en `tecnologia/backend/tests/{unitarias,integracion}/`
- Frontend: `tecnologia/frontend/src/`, pruebas en `tecnologia/frontend/tests/`
- Pruebas externas: `tecnologia/pruebas/{postman,k6}/` · Evidencias: `evidencias/EQ-0X/`

---

## Phase 1: Setup (Día 1)

**Purpose**: estructura del repositorio, herramientas y entorno reproducible.

- [X] T001 Crear la estructura de `plan.md` → Project Structure: `tecnologia/backend/app/core/`, `tecnologia/backend/app/modules/{identity,catalog,requests,rules,signing,inventory,audit}/{dominio,aplicacion,infraestructura,presentacion}/` (cada una con `__init__.py`), `tecnologia/backend/tests/{unitarias,integracion}/`, `tecnologia/backend/{migrations,seeds,scripts}/`, `tecnologia/pruebas/{postman,k6}/` `evidencias/EQ-01/` … `evidencias/EQ-09/` y `evidencias/SC-009/`, cada una con `.gitkeep`
- [X] T002 Crear `tecnologia/backend/pyproject.toml` con Python 3.12; dependencias FastAPI, uvicorn, Pydantic v2, pydantic-settings, SQLAlchemy 2.0, Alembic, psycopg[binary] 3, cryptography, PyJWT y bcrypt; extras `dev` con pytest, httpx, pytest-cov y Ruff; configuración de Ruff, `[tool.pytest.ini_options]` y `[tool.coverage]` con `source` en `app/modules/{requests,rules,signing,inventory}` y `fail_under = 60`
- [X] T003 [P] Crear `tecnologia/.env.example` con `DATABASE_URL`, `DATABASE_URL_TEST`, `JWT_SECRETO`, `JWT_MINUTOS=60`, `FIRMA_CLAVE_PRIVADA`, `FIRMA_CLAVE_ID`, `UMBRAL_MONTO_ALTO=50000`, `CATALOGO_CACHE_ACTIVA=true` y `CONTRASENA_DEMO`, todas sin valores secretos, y agregar `.env`, `htmlcov/`, `coverage/`, `.coverage` y `node_modules/` al `.gitignore` de la raíz
- [X] T004 [P] Crear `tecnologia/backend/Dockerfile` (python:3.12-slim, instala el paquete y arranca `uvicorn app.main:app --host 0.0.0.0 --port 8000`)
- [X] T005 [P] Crear el frontend React 18 + TypeScript + Vite en `tecnologia/frontend/`: `package.json` con los scripts `dev`, `build`, `lint`, `test` y `test:cov`, `tsconfig.json`, `vite.config.ts` con proxy de `/api` a `http://localhost:8000`, configuración de ESLint y dependencia de React Router
- [X] T006 [P] Configurar Jest en `tecnologia/frontend/jest.config.ts`: ts-jest, `testEnvironment: jsdom`, `setupFilesAfterEnv` → `tests/setup.ts` con `@testing-library/jest-dom`, `moduleNameMapper` para `src/config.ts` y para CSS con `identity-obj-proxy`, y `coverageThreshold` global de 60 % sobre `src/logica`, `src/auth` y `src/api` (research §12). Crear `tecnologia/frontend/src/config.ts`, que es la única lectura de `import.meta.env`, con su primera prueba en `tecnologia/frontend/tests/config.test.ts`
- [X] T007 [P] Crear `tecnologia/frontend/Dockerfile` (build con Node 20 y después nginx:alpine) y `tecnologia/nginx/default.conf`: sirve `dist/` con `Cache-Control: max-age=31536000, immutable` para los archivos con huella, usa `try_files` hacia `index.html` y reenvía `/api/`, `/docs`, `/openapi.json` y `/health` a `api:8000` (research §7, ADR-012)
- [X] T008 Crear `tecnologia/docker-compose.yml` con los servicios `db` (postgres:16, volumen y healthcheck con `pg_isready`), `api` (build `backend/`, `env_file: .env`, `restart: always`, healthcheck sobre `/health`, ADR-013) y `web` (build `frontend/`, puerto 8080, depende de `api`)
- [X] T009 [P] Crear `.github/workflows/ci.yml` que se ejecute en `push` y `pull_request`, con dos trabajos. **backend**: servicio postgres:16, `pip install -e tecnologia/backend[dev]`, `ruff check`, `ruff format --check`, `alembic upgrade head`, `pytest --cov --cov-report=xml --cov-report=html` y subida de los artefactos. **frontend**: Node 20, `npm ci`, `npm run lint`, `npx tsc --noEmit`, `npm run test:cov`, `npm run build` y subida de `coverage/` (plan → CI)

**Checkpoint**: `docker compose up` levanta los tres contenedores y el CI corre, aunque todavía no tenga pruebas de dominio.

---

## Phase 2: Foundational (Día 1, y el frontend base al inicio del Día 2)

**Purpose**: base que bloquea a todas las historias: configuración, base de datos, migraciones, seeds, sesión, catálogo, auditoría y dominio.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

### Núcleo y persistencia

- [ ] T010 Implementar la configuración en `tecnologia/backend/app/core/config.py` con pydantic-settings y las variables de T003
- [ ] T011 Implementar el motor, la sesión y el pool de conexiones en `tecnologia/backend/app/core/base_datos.py` (`pool_size=10`, `max_overflow=10`, `pool_pre_ping=True`)
- [ ] T012 Implementar la Unidad de Trabajo en `tecnologia/backend/app/core/unidad_trabajo.py`: un administrador de contexto que hace `commit` si todo sale bien y `rollback` ante cualquier excepción, más su dependencia de FastAPI (ADR-003)
- [ ] T013 Implementar los errores en `tecnologia/backend/app/core/errores.py`: la jerarquía `ErrorNegocio` (`NoAutenticado` 401, `SinPermiso` 403, `NoEncontrado` 404, `Conflicto` 409 con `codigo`) y los manejadores que responden con el esquema `Error` del contrato (`codigo`, `mensaje` en español, `detalles`). Incluir un manejador de `RequestValidationError` que devuelva 422 con un mensaje por campo
- [ ] T014 Configurar Alembic en `tecnologia/backend/alembic.ini` y `tecnologia/backend/migrations/env.py`, tomando `DATABASE_URL` de la configuración y los metadatos de todos los módulos
- [ ] T015 [P] Crear los modelos de `tecnologia/backend/app/modules/catalog/infraestructura/modelos.py` según `data-model.md organo.codigo`, `organo.tipo`, `organo.padre_id`, `almacen.organo_id`, `almacen.categoria`, `item.codigo`, `item.categoria`, `item.unidad_medida`, `item.valor_unitario` e `item.activo`
- [ ] T016 [P] Crear el modelo de `tecnologia/backend/app/modules/identity/infraestructura/modelos.py` según `data-model.md usuario.usuario`, `usuario.hash_contrasena`, `usuario.rol`, `usuario.organo_id`, `usuario.almacen_id` y `usuario.activo`
- [ ] T017 [P] Crear los modelos de `tecnologia/backend/app/modules/inventory/infraestructura/modelos.py` según `data-model.md stock.almacen_id`, `stock.item_id`, `stock.cantidad`, `movimiento.almacen_id`, `movimiento.item_id`, `movimiento.tipo`, `movimiento.cantidad`, `movimiento.requerimiento_id` y `movimiento.usuario_id`
- [ ] T018 [P] Crear los modelos de `tecnologia/backend/app/modules/requests/infraestructura/modelos.py` según `data-model.md requerimiento.codigo`, `requerimiento.unidad_id`, `requerimiento.gran_unidad_id`, `requerimiento.almacen_id`, `requerimiento.categoria`, `requerimiento.estado`, `requerimiento.monto_total`, `requerimiento.creado_por`, `requerimiento.version`, `item_requerimiento.item_id`, `item_requerimiento.cantidad_solicitada`, `item_requerimiento.cantidad_despachada`, `item_requerimiento.cantidad_recibida`, `item_requerimiento.observacion`, `historial_requerimiento.accion`, `historial_requerimiento.estado_anterior`, `historial_requerimiento.estado_nuevo`, `historial_requerimiento.usuario_id`, `historial_requerimiento.rol` (enum `Rol`), `historial_requerimiento.organo_id` e `historial_requerimiento.motivo`
- [ ] T019 [P] Crear los modelos de `tecnologia/backend/app/modules/signing/infraestructura/modelos.py` según `data-model.md firma.nivel`, `firma.decision`, `firma.firmante_id`, `firma.rol` (enum `Rol`), `firma.organo_id`, `firma.contenido_canonico`, `firma.huella_sha256`, `firma.firma`, `firma.metodo`, `firma.clave_id`, `firma.firmado_en`, `acta_recepcion.requerimiento_id`, `acta_recepcion.firma_id` y `acta_recepcion.tiene_diferencias`, incluida la restricción única `(requerimiento_id, nivel)`
- [ ] T020 [P] Crear el modelo de `tecnologia/backend/app/modules/audit/infraestructura/modelos.py` según `data-model.md registro_auditoria.tipo_evento`, `registro_auditoria.entidad`, `registro_auditoria.entidad_id`, `registro_auditoria.usuario_id`, `registro_auditoria.rol`, `registro_auditoria.organo_id`, `registro_auditoria.datos`, `registro_auditoria.huella_anterior` y `registro_auditoria.huella`
- [ ] T021 Crear la migración `tecnologia/backend/migrations/versions/0001_esquema_inicial.py`: todas las tablas y enums de T015–T020, las restricciones `CHECK`, `UNIQUE` y `FK` de data-model.md, y los índices de data-model.md §8. Incluye las FK de `data-model.md movimiento.almacen_id`, `movimiento.item_id`, `movimiento.usuario_id`, `requerimiento.creado_por`, `historial_requerimiento.usuario_id`, `historial_requerimiento.organo_id`, `firma.firmante_id`, `firma.organo_id` y `acta_recepcion.firma_id` (apunta a una firma de nivel ACTA_RECEPCION, que también valida T076), y el enum `Rol` en `historial_requerimiento.rol`, `firma.rol` y `registro_auditoria.rol`
- [ ] T022 Crear la migración `tecnologia/backend/migrations/versions/0002_inmutabilidad.py`. Agrega disparadores que rechacen `UPDATE` y `DELETE` sobre `firma`, `acta_recepcion`, `movimiento`, `historial_requerimiento` y `registro_auditoria`, y sobre `requerimiento` e `item_requerimiento` cuando `data-model.md requerimiento.estado` es final (CONFIRMADA, RECHAZADA o ANULADA), según data-model.md §4 → *Protección del acta*. En `requerimiento`, el disparador evalúa **`OLD.estado`**, no `NEW.estado`, para no bloquear la propia transición a un estado final. En `item_requerimiento`, consulta el estado actual del requerimiento padre; por eso T076 escribe los ítems antes de cambiar el estado
- [ ] T023 Implementar `tecnologia/backend/seeds/cargar.py`, idempotente, según data-model.md §9: órganos, almacenes, ítems con valor unitario, stock inicial como movimientos `ENTRADA` y usuarios con los nombres de `quickstart.md` §3. La contraseña sale de `CONTRASENA_DEMO`, con hash bcrypt
- [ ] T024 [P] Implementar `tecnologia/backend/scripts/generar_clave_firma.py`: genera un par Ed25519 e imprime `FIRMA_CLAVE_PRIVADA` (PEM en base64) y `FIRMA_CLAVE_ID`

### Identidad, catálogo, salud y auditoría

- [ ] T025 Implementar la seguridad en `tecnologia/backend/app/core/seguridad.py`: crear y decodificar el JWT con `sub`, `rol` y `organo_id` (HS256, `JWT_MINUTOS`), la dependencia `usuario_actual` (401 si falta el token o es inválido) y `requiere_rol(*roles)` (403), según research §4
- [ ] T026 Implementar el inicio de sesión: `tecnologia/backend/app/modules/identity/dominio/rol.py` (enum según `data-model.md usuario.rol`), `.../identity/aplicacion/iniciar_sesion.py` (verifica bcrypt y rechaza a los usuarios inactivos) y `.../identity/presentacion/router.py` con `POST /api/v1/auth/login` y `GET /api/v1/auth/me`, según `contracts/openapi.yaml`
- [ ] T027 [P] Implementar el catálogo: `tecnologia/backend/app/modules/catalog/aplicacion/consultar_catalogo.py` (ítems activos por categoría y estructura orgánica, con caché en memoria con TTL de 300 s que se desactiva con `CATALOGO_CACHE_ACTIVA=false`, research §7) y `.../catalog/presentacion/router.py` con `GET /api/v1/catalogo/items` y la cabecera `Cache-Control: private, max-age=300`
- [ ] T028 Implementar la auditoría encadenada: `tecnologia/backend/app/modules/audit/dominio/puertos.py` (`RegistroAuditoria`) y `.../audit/infraestructura/registro_encadenado.py`, que toma `pg_advisory_xact_lock`, lee la última huella y calcula `data-model.md registro_auditoria.huella` a partir de `registro_auditoria.huella_anterior` y el JSON canónico, dentro de la transacción de quien lo llama (research §6)
- [ ] T029 Implementar `/health` en `tecnologia/backend/app/core/salud.py`, que hace `SELECT 1` y responde `base_datos` OK o ERROR, y la raíz de composición en `tecnologia/backend/app/main.py`: registra los routers, los manejadores de errores y el título y la versión de OpenAPI, para que Swagger quede disponible en `/docs`

### Dominio (reglas críticas)

- [ ] T030 Implementar el dominio de requerimientos en `tecnologia/backend/app/modules/requests/dominio/`:
  - `estado.py`, con el enum según `data-model.md requerimiento.estado`.
  - `errores.py`, con `TransicionNoPermitida`, `NivelYaFirmado`, `RequiereCologe`, `MotivoObligatorio` y `CantidadInvalida`.
  - `requerimiento.py`, con la entidad y el patrón State. Implementa todas las transiciones de data-model.md §6 (crear, editar, enviar, anular, firmar o rechazar por nivel, despachar y firmar el acta); valida `data-model.md item_requerimiento.cantidad_solicitada`, `item_requerimiento.cantidad_despachada` e `item_requerimiento.cantidad_recibida`, la clave sin ítems repetidos y la categoría única; y aumenta `data-model.md requerimiento.version` en cada transición. Es Python puro, sin importar FastAPI ni SQLAlchemy
- [ ] T031 [P] Implementar la regla RN03 en `tecnologia/backend/app/modules/rules/dominio/regla_aprobacion.py`: el protocolo `ReglaAprobacion` y la estrategia `ReglaCologePorCategoriaOMonto`, que exige COLOGE si `data-model.md requerimiento.categoria` es MATERIAL_GUERRA o si `requerimiento.monto_total` ≥ `UMBRAL_MONTO_ALTO` (patrón Strategy, plan → SOLID)
- [ ] T032 [P] Prueba unitaria en `tecnologia/backend/tests/unitarias/test_requerimiento_estados.py`:
  - Cada transición válida de data-model.md §6.
  - Toda transición no listada lanza `TransicionNoPermitida`.
  - Un nivel no firma dos veces.
  - Rechazar sin motivo falla.
  - Solo se anula desde BORRADOR.
  - Las cantidades fuera de rango fallan.
- [ ] T033 [P] Prueba unitaria en `tecnologia/backend/tests/unitarias/test_regla_aprobacion.py`: intendencia bajo el umbral no exige COLOGE; material de guerra sí; intendencia en el umbral exacto o por encima sí
- [ ] T034 Crear `tecnologia/backend/tests/integracion/conftest.py` con estos fixtures:
  - Base de datos de prueba (`DATABASE_URL_TEST`) con `alembic upgrade head` y seeds.
  - `TRUNCATE … CASCADE` de las tablas de negocio entre pruebas, por las claves foráneas. No hace falta desactivar los disparadores, porque `TRUNCATE` no activa los disparadores por fila de `UPDATE` y `DELETE`.
  - `TestClient` de httpx.
  - `login(usuario)`, que devuelve las cabeceras con el token.
  - El firmador real con una clave generada en memoria.
- [ ] T035 [P] Prueba de integración en `tecnologia/backend/tests/integracion/test_identidad.py`:
  - Inicio de sesión correcto.
  - Contraseña incorrecta → 401.
  - `/auth/me` con token y sin token (401).
  - Token expirado → 401.
  - `/health` responde OK.
  - `/docs` y `/openapi.json` responden 200.
  - `GET /catalogo/items` con su cabecera `Cache-Control`.

### Frontend base (inicio del Día 2)

- [ ] T036 [P] Implementar el cliente de la API en `tecnologia/frontend/src/api/cliente.ts`: `fetch` con la URL de `src/config.ts`, cabecera `Authorization`, conversión de las respuestas de error al esquema `Error` y evento de cierre de sesión ante un 401. Los tipos van en `tecnologia/frontend/src/api/tipos.ts`, tomados de `contracts/openapi.yaml`
- [ ] T037 [P] Implementar `tecnologia/frontend/src/logica/estados.ts`, con las etiquetas de la tabla de estados de `spec.md`, y `tecnologia/frontend/src/logica/mensajes.ts`, con los mensajes en español por `codigo` de error (TRANSICION_NO_PERMITIDA, NIVEL_YA_FIRMADO, REQUIERE_COLOGE, STOCK_INSUFICIENTE y ESTADO_CAMBIADO) y por código HTTP
- [ ] T038 Implementar la sesión en `tecnologia/frontend/src/auth/SesionContexto.tsx` (token y usuario en memoria y `sessionStorage`, más `cerrarSesion`) y `tecnologia/frontend/src/auth/RutaProtegida.tsx` (redirige al inicio de sesión sin sesión y bloquea los roles no permitidos)
- [ ] T039 [P] Crear los componentes base en `tecnologia/frontend/src/componentes/`: `Mensaje.tsx` (error, éxito, aviso), `Cargando.tsx`, `EstadoEtiqueta.tsx` y `Formulario.tsx`; y los estilos responsive en `tecnologia/frontend/src/estilos.css`, pensados primero para celular y con un solo punto de corte
- [ ] T040 [P] Prueba Jest en `tecnologia/frontend/tests/api/cliente.test.ts`: agrega el token; un 401 dispara el cierre de sesión; 403, 404, 409 y 422 se convierten en mensajes en español; los errores de red muestran un mensaje genérico
- [ ] T041 [P] Prueba Jest en `tecnologia/frontend/tests/auth/RutaProtegida.test.tsx`: sin sesión redirige; con un rol no permitido no muestra la página; con un rol permitido sí la muestra

**Checkpoint**: inicio de sesión por Swagger, CI en verde con pytest y Jest, y todas las transiciones de dominio probadas.

---

## Phase 3: User Story 1 — Registrar y enviar una solicitud (Priority: P1) 🎯 MVP · Día 2

**Goal**: el oficial de logística registra, edita, envía y lista sus solicitudes; las que requieren al COLOGE quedan bloqueadas al enviarlas (FR-005 a FR-008, FR-012).

**Independent Test**: con los seeds, `oficial.bim11` crea y envía una solicitud de intendencia y la ve en su bandeja en estado PENDIENTE_VB_UNIDAD. Una de material de guerra queda en BORRADOR con el aviso del COLOGE.

### Tests for User Story 1

- [ ] T042 [P] [US1] Prueba de integración en `tecnologia/backend/tests/integracion/test_registro_envio.py` con los escenarios 1 a 6 de la US1 de `spec.md`:
  - Crear y enviar.
  - Guardar en BORRADOR.
  - Sin ítems, cantidad 0 o ítem repetido → 422.
  - Un rol distinto → 403.
  - Material de guerra → 409 REQUIERE_COLOGE, con `ENVIO_BLOQUEADO` en el historial y el estado sin cambiar.
  - Monto en el umbral → 409.
  - Ítem inactivo → 422.
  - Editar fuera de BORRADOR → 409.
  - La bandeja paginada solo muestra lo de su unidad.
- [ ] T043 [P] [US1] Prueba Jest en `tecnologia/frontend/tests/logica/validacionSolicitud.test.ts`: al menos un ítem, cantidad entera > 0, sin ítems repetidos, una sola categoría y 5 campos visibles como máximo

### Implementation for User Story 1

- [ ] T044 [US1] Definir los puertos en `tecnologia/backend/app/modules/requests/dominio/puertos.py` (`RepositorioRequerimientos`, `ConsultaCatalogo` y `RegistroAuditoria`) e implementarlos en `.../requests/infraestructura/repositorio_postgres.py`:
  - `obtener_para_actualizar` con `SELECT … FOR UPDATE`.
  - `guardar`.
  - `agregar_historial`, según `data-model.md historial_requerimiento.accion` y `historial_requerimiento.motivo`.
  - `listar_paginado`, usando los índices de data-model.md §8.

  Registrar los adaptadores en `.../requests/infraestructura/dependencias.py`.
- [ ] T045 [US1] Implementar la política de acceso en `tecnologia/backend/app/modules/requests/aplicacion/politica_acceso.py`: la visibilidad por rol de data-model.md §7 (lo ajeno responde 404, FR-002 y FR-003) y el cálculo de `acciones_disponibles` para el usuario actual
- [ ] T046 [US1] Implementar `tecnologia/backend/app/modules/requests/aplicacion/registrar_requerimiento.py`, con las operaciones registrar y editar:
  - Deduce `data-model.md requerimiento.unidad_id`, `requerimiento.gran_unidad_id` (el padre de la unidad) y `requerimiento.almacen_id` (el de la categoría).
  - Genera `requerimiento.codigo` con el formato `REQ-AAAA-NNNNNN`.
  - Valida que `item_requerimiento.item_id` esté activo y sea de la categoría.
  - Registra `CREAR` en el historial y en la auditoría.
  - Todo en una Unidad de Trabajo (FR-005 a FR-008).
- [ ] T047 [US1] Implementar `tecnologia/backend/app/modules/requests/aplicacion/enviar_requerimiento.py`:
  - Calcula `data-model.md requerimiento.monto_total`.
  - Consulta `ReglaAprobacion` (T031).
  - Si se exige el COLOGE, registra `ENVIO_BLOQUEADO` con su motivo, confirma la transacción y lanza `RequiereCologe` (409).
  - Si no, pasa a PENDIENTE_VB_UNIDAD con su historial y su auditoría (FR-012).
- [ ] T048 [US1] Implementar `tecnologia/backend/app/modules/requests/aplicacion/consultar_requerimientos.py`, con la bandeja paginada (`page` y `size` ≤ 50, filtro por `estado`) y el detalle con `acciones_disponibles` (FR-029)
- [ ] T049 [US1] Implementar `tecnologia/backend/app/modules/requests/presentacion/esquemas.py` y `router.py` con `GET` y `POST /api/v1/requerimientos`, `GET` y `PUT /api/v1/requerimientos/{id}` y `POST /api/v1/requerimientos/{id}/enviar`, según `contracts/openapi.yaml`; y registrarlo en `tecnologia/backend/app/main.py`
- [ ] T050 [P] [US1] Implementar `tecnologia/frontend/src/logica/validacionSolicitud.ts`, con las reglas que prueba T043
- [ ] T051 [US1] Implementar `tecnologia/frontend/src/paginas/InicioSesion.tsx`: usuario y contraseña, validación, estado de carga y mensaje ante un 401. Después de entrar, redirige a la bandeja
- [ ] T052 [US1] Implementar `tecnologia/frontend/src/paginas/NuevaSolicitud.tsx`:
  - Campos: categoría, ítem, cantidad y agregar o quitar ítem; 5 campos como máximo por pantalla.
  - Usa la validación de T050.
  - Botones Guardar y Enviar.
  - Muestra el aviso de COLOGE ante REQUIERE_COLOGE.
  - Muestra el estado de carga mientras espera la respuesta.
- [ ] T053 [US1] Configurar las rutas en `tecnologia/frontend/src/App.tsx` y `tecnologia/frontend/src/main.tsx` (`/ingresar`, `/bandeja`, `/solicitudes/nueva` y `/solicitudes/:id`) con `RutaProtegida` por rol, y crear una `Bandeja.tsx` mínima, solo una lista con su estado, en `tecnologia/frontend/src/paginas/Bandeja.tsx`
- [ ] T054 [P] [US1] Pruebas Jest en `tecnologia/frontend/tests/paginas/InicioSesion.test.tsx` y `NuevaSolicitud.test.tsx`, con `fetch` simulado:
  - Inicio de sesión correcto y erróneo.
  - El envío bloqueado muestra el aviso del COLOGE.
  - Los errores 422 se muestran por campo.
  - El botón queda desactivado mientras carga.

**Checkpoint**: registrar y enviar desde la web (demostrable al final del Día 2).

---

## Phase 4: User Story 2 — Aprobar o rechazar por el conducto regular (Priority: P1) · Día 2 (backend) y Día 3 (frontend)

**Goal**: el comandante de la unidad y el jefe de logística de la División/Brigada firman con Ed25519 o rechazan con motivo; ningún nivel se omite y nadie de otra jurisdicción actúa (FR-009 a FR-016).

**Independent Test**: una solicitud enviada recibe el visto bueno de `cmdte.bim11` y la conformidad de `jlog.1de`. `jlog.2de` recibe 404, y firmar dos veces da 409.

### Tests for User Story 2

- [ ] T055 [P] [US2] Prueba unitaria en `tecnologia/backend/tests/unitarias/test_firma.py` (EQ-02, parte unitaria):
  - El contenido canónico es estable aunque cambie el orden de las claves.
  - Firmar y verificar con Ed25519 da INTEGRA.
  - Cambiar un byte del contenido o de la firma da ALTERADA.
  - Se guardan `metodo` y `clave_id`.
- [ ] T056 [P] [US2] Prueba de integración en `tecnologia/backend/tests/integracion/test_conducto_regular.py` con los escenarios 1 a 6 de la US2:
  - Visto bueno.
  - Conformidad.
  - Conformidad antes del visto bueno → 409.
  - Jefe de otra División → 404.
  - Rechazo sin motivo → 422; con motivo → RECHAZADA, y después ninguna acción más.
  - Doble firma → 409 NIVEL_YA_FIRMADO.
  - Dos firmas concurrentes en dos hilos → una sola se registra y la otra recibe 409 ESTADO_CAMBIADO.
- [ ] T057 [US2] Prueba de integración EQ-01, parte de envío y firmas (Día 2), en `tecnologia/backend/tests/integracion/test_eq01_control_acceso.py`. Es una matriz parametrizada que T098 amplía el Día 3 con el despacho y el acta:
  - Cada rol intenta cada acción que no le corresponde entre enviar y firmar o rechazar en cada nivel (VB_UNIDAD, CONFORMIDAD_GU y APROBACION_ALMACEN) y espera 403 o 409.
  - Sin token, espera 401.
  - Cada rol consulta una solicitud de otra unidad o jurisdicción y espera 404.
  - Un BORRADOR solo lo ven los oficiales de logística de su unidad: el comandante, el jefe de la Gran Unidad, el almacén y el auditor reciben 404 (data-model.md §7).
  - Un usuario sin unidad o sin jurisdicción, creado en el fixture (por ejemplo, un JEFE_ALMACEN sin `almacen_id` o un COMANDANTE_UNIDAD cuyo órgano no es una UNIDAD), recibe una bandeja vacía y 404 en cualquier solicitud (caso límite de `spec.md`).
  - Debe cumplirse en el 100 % de los casos.
  - El resumen se guarda en `evidencias/EQ-01/`.

### Implementation for User Story 2

- [ ] T058 [US2] Implementar `tecnologia/backend/app/modules/signing/dominio/contenido_canonico.py` (JSON ordenado y compacto en UTF-8, y huella SHA-256 hexadecimal, research §3) y `.../signing/dominio/puertos.py` (`FirmadorDocumentos`: `firmar(bytes)` y `verificar(bytes, firma, clave_id)`)
- [ ] T059 [P] [US2] Implementar `tecnologia/backend/app/modules/signing/infraestructura/firmador_ed25519.py` con la librería `cryptography`. La clave sale de `FIRMA_CLAVE_PRIVADA` y el `metodo` es `ed25519-sha256-v1`. Agregar `tecnologia/backend/tests/firmador_falso.py`, un doble de prueba que cumple el mismo puerto (Liskov)
- [ ] T060 [US2] Implementar `tecnologia/backend/app/modules/signing/aplicacion/servicio_firma.py`. La operación `firmar_nivel` construye el contenido canónico con los campos fijos de research §3:
  - En VB_UNIDAD, CONFORMIDAD_GU y APROBACION_ALMACEN: `id`, `codigo`, `unidad_id` y `categoria` de la solicitud; los ítems con `item_id` y `cantidad_solicitada`; y el nivel, la decisión, el firmante, su rol, su órgano y la fecha y hora.
  - En ACTA_RECEPCION, además, por ítem: `cantidad_despachada`, `cantidad_recibida` y `observacion`.
  - **Nunca** se firman `estado` ni `version`, para que el despacho y el acta no invaliden las firmas anteriores.

  Después firma y guarda según `data-model.md firma.nivel`, `firma.decision`, `firma.huella_sha256`, `firma.metodo` y `firma.clave_id`, dentro de la Unidad de Trabajo de quien la llama
- [ ] T061 [US2] Implementar `tecnologia/backend/app/modules/requests/aplicacion/firmar_requerimiento.py`, en una sola Unidad de Trabajo:
  - Bloquea la solicitud y comprueba la jurisdicción con la política de T045.
  - Deduce el nivel a partir del estado: PENDIENTE_VB_UNIDAD da VB_UNIDAD, PENDIENTE_CONFORMIDAD da CONFORMIDAD_GU y PENDIENTE_APROBACION da APROBACION_ALMACEN.
  - Valida el rol y el órgano del firmante.
  - Aplica la transición del dominio, con motivo obligatorio para rechazar.
  - Firma (T060) y registra el historial y la auditoría.
  - Convierte la violación de la restricción única en NIVEL_YA_FIRMADO y la carrera de estados en ESTADO_CAMBIADO.
- [ ] T062 [US2] Agregar `GET` y `POST /api/v1/requerimientos/{id}/firmas` en `tecnologia/backend/app/modules/requests/presentacion/router.py`, con los esquemas `DecisionFirma` y `Firma` de `contracts/openapi.yaml`
- [ ] T063 [US2] Completar `tecnologia/frontend/src/paginas/Bandeja.tsx`: lista paginada según el rol, filtro por estado, etiquetas de estado y estados de carga y de lista vacía
- [ ] T064 [US2] Implementar `tecnologia/frontend/src/paginas/DetalleSolicitud.tsx`: datos e ítems, y los botones **Firmar** y **Rechazar**, que solo aparecen si `acciones_disponibles` los incluye. Rechazar abre un diálogo con el motivo obligatorio. Lo apoya `tecnologia/frontend/src/logica/acciones.ts`
- [ ] T065 [P] [US2] Pruebas Jest en `tecnologia/frontend/tests/logica/acciones.test.ts` y `tecnologia/frontend/tests/paginas/DetalleSolicitud.test.tsx`:
  - Solo aparecen las acciones permitidas.
  - Rechazar sin motivo no envía.
  - Un 409 muestra un mensaje comprensible.
  - Después de firmar se recarga el detalle.

**Checkpoint**: todo el conducto regular de la unidad y la División/Brigada, desde la web (Día 3).

---

## Phase 5: User Story 3 — Aprobar la atención y despachar sin superar el stock (Priority: P1) · Día 3 (backend) y Día 4 (frontend)

**Goal**: el jefe de almacén aprueba con firma o rechaza, y el almacenero despacha descontando el stock en una sola transacción con bloqueo (FR-011, FR-017 a FR-020).

**Independent Test**: una solicitud en PENDIENTE_APROBACION se aprueba con `jalm.sinte` y se despacha con `almacenero.sinte`. El stock baja exactamente lo enviado, y dos despachos simultáneos que superan el stock dejan un solo despacho registrado.

### Tests for User Story 3

- [ ] T066 [P] [US3] Prueba de integración en `tecnologia/backend/tests/integracion/test_despacho.py` con los escenarios 1 a 4 y 6 de la US3:
  - El jefe de almacén aprueba y la solicitud queda APROBADA.
  - Si rechaza, queda RECHAZADA.
  - Un despacho de 7 con stock 10 deja el stock en 3 y crea un movimiento.
  - Con stock insuficiente responde 409 STOCK_INSUFICIENTE y nada cambia.
  - Despachar algo que no está APROBADA → 409.
  - Despachar más de lo solicitado → 422.
  - El despacho parcial se registra con lo despachado.
- [ ] T067 [P] [US3] Prueba de integración EQ-03 en `tecnologia/backend/tests/integracion/test_eq03_concurrencia.py`:
  - Dos hilos, cada uno con su propia conexión, despachan 7 y 7 de un ítem con stock 10.
  - Exactamente uno da 201 y el otro 409.
  - El stock final es 3.
  - La consulta SQL que compara `stock.cantidad` con Σ movimientos por (almacén, ítem) da 0 diferencias (`data-model.md stock.cantidad`, invariante EQ-03).
  - El resultado se guarda en `evidencias/EQ-03/`.

### Implementation for User Story 3

- [ ] T068 [US3] Implementar `tecnologia/backend/app/modules/inventory/aplicacion/servicio_despacho.py`, con su puerto en `.../inventory/dominio/puertos.py`:
  - Bloquea las filas de `stock` con `FOR UPDATE`, ordenadas por `item_id`.
  - Valida que haya stock suficiente según `data-model.md stock.cantidad`.
  - Inserta los movimientos según `data-model.md movimiento.tipo` (SALIDA_DESPACHO), `movimiento.cantidad` y `movimiento.requerimiento_id`.
  - Descuenta el stock.
  - Todo dentro de la Unidad de Trabajo de quien lo llama (ADR-003).
- [ ] T069 [US3] Implementar `tecnologia/backend/app/modules/requests/aplicacion/despachar_requerimiento.py`. Solo actúa el ALMACENERO del `data-model.md requerimiento.almacen_id`. Valida que `item_requerimiento.cantidad_despachada` no supere lo solicitado y que al menos un ítem tenga una cantidad mayor que 0, llama a T068, pasa a EN_TRANSITO y registra el historial y la auditoría en una sola transacción
- [ ] T070 [US3] Agregar `POST /api/v1/requerimientos/{id}/despacho` en `tecnologia/backend/app/modules/requests/presentacion/router.py`, y `GET /api/v1/inventario/stock`, paginado y solo para el almacén del usuario, en `tecnologia/backend/app/modules/inventory/presentacion/router.py`; registrarlos en `main.py`
- [ ] T071 [US3] Agregar en `tecnologia/frontend/src/paginas/DetalleSolicitud.tsx` el formulario **Despachar**: una cantidad por ítem, con lo solicitado como valor inicial y un máximo igual a lo solicitado, y un mensaje claro ante STOCK_INSUFICIENTE (Día 4)
- [ ] T072 [P] [US3] Implementar `tecnologia/frontend/src/paginas/Stock.tsx`, una tabla paginada del stock del almacén para JEFE_ALMACEN y ALMACENERO (Día 4; es lo primero que se recorta si falta tiempo)
- [ ] T073 [P] [US3] Prueba Jest en `tecnologia/frontend/tests/paginas/Despacho.test.tsx`: no deja enviar una cantidad mayor que la solicitada, y STOCK_INSUFICIENTE muestra su mensaje (Día 4)

**Checkpoint**: aprobación del almacén y despacho con un stock consistente.

---

## Phase 6: User Story 4 — Firmar el acta de recepción y verificar su integridad (Priority: P1) · Día 3 (backend) y Día 4 (frontend)

**Goal**: el oficial de logística de la unidad solicitante firma el acta con lo recibido y sus diferencias. El acta queda inmutable y cualquier usuario autorizado la verifica (FR-021, FR-023 a FR-025).

**Independent Test**: una solicitud EN_TRANSITO pasa a CONFIRMADA al firmar el acta; `/verificacion` responde INTEGRA y, si se altera un dato firmado, ALTERADA.

### Tests for User Story 4

- [ ] T074 [P] [US4] Prueba de integración en `tecnologia/backend/tests/integracion/test_acta.py` con los escenarios 1 a 4 y 6 de la US4:
  - El acta registra lo recibido y las diferencias, con `tiene_diferencias` correcto.
  - Un oficial de otra unidad o de otro rol → 403 o 404.
  - Volver a firmar → 409.
  - Hacer `UPDATE` sobre el acta o sus ítems en la base de datos es rechazado por el disparador.
  - Firmar algo que no está EN_TRANSITO → 409.
  - La verificación responde INTEGRA, con el firmante y la fecha.
- [ ] T075 [P] [US4] Prueba de integración EQ-02 en `tecnologia/backend/tests/integracion/test_eq02_integridad.py`. Para cada campo firmado (cantidad recibida, cantidad solicitada, firmante y fecha), desactiva el disparador dentro de la prueba, altera el dato en la base de datos y comprueba que `/verificacion` responde ALTERADA en el 100 % de los casos. Incluye el caso contrario, para descartar falsos positivos: después del despacho (EN_TRANSITO) y otra vez después del acta (CONFIRMADA), las firmas VB_UNIDAD, CONFORMIDAD_GU y APROBACION_ALMACEN siguen dando INTEGRA. El resumen se guarda en `evidencias/EQ-02/`
- [ ] T098 [US4] Ampliar la matriz EQ-01 de T057 en `tecnologia/backend/tests/integracion/test_eq01_control_acceso.py` con despachar y firmar el acta (Día 3, cuando ya existen T070 y T078). Cada rol al que no le corresponde la acción espera 403 o 409, y un ALMACENERO de otro almacén o un OFICIAL_LOGISTICA de otra unidad espera 404. Actualiza el resumen de `evidencias/EQ-01/`

### Implementation for User Story 4

- [ ] T076 [US4] Implementar `tecnologia/backend/app/modules/requests/aplicacion/confirmar_recepcion.py`. Solo actúa el OFICIAL_LOGISTICA de `data-model.md requerimiento.unidad_id`, con la solicitud EN_TRANSITO. Todo va en una sola transacción y **en este orden**, primero los ítems y luego el estado, porque el disparador de T022 bloquea los ítems cuando el requerimiento ya está en un estado final:
  1. Registra `item_requerimiento.cantidad_recibida` e `item_requerimiento.observacion`.
  2. Firma el nivel ACTA_RECEPCION con el contenido canónico del acta de research §3, que agrega lo despachado, lo recibido y las observaciones (T060).
  3. Crea el acta según `data-model.md acta_recepcion.requerimiento_id`, `acta_recepcion.firma_id` (la firma del paso 2) y `acta_recepcion.tiene_diferencias`.
  4. Por último, pasa a CONFIRMADA y registra el historial y la auditoría.
- [ ] T077 [US4] Implementar `tecnologia/backend/app/modules/signing/aplicacion/verificar_requerimiento.py`. Para cada firma, reconstruye el contenido canónico con los datos **actuales** de la base de datos y con los mismos campos que usa T060 para ese nivel (research §3: sin `estado` ni `version`, y con lo despachado, lo recibido y las observaciones solo en ACTA_RECEPCION). Luego recalcula la huella y verifica la firma según `metodo`. Devuelve INTEGRA o ALTERADA por firma y el resultado global (FR-024, FR-025)
- [ ] T078 [US4] Agregar `POST` y `GET /api/v1/requerimientos/{id}/acta` y `GET /api/v1/requerimientos/{id}/verificacion` en `tecnologia/backend/app/modules/requests/presentacion/router.py`, según `contracts/openapi.yaml`. El AUDITOR puede consultar y verificar
- [ ] T079 [US4] Agregar en `tecnologia/frontend/src/paginas/DetalleSolicitud.tsx` el formulario **Firmar acta** (cantidad recibida y observación por ítem, resaltando las diferencias) y el botón **Verificar**, que muestra Íntegra o Alterada por firma junto con el firmante y la fecha (Día 4)
- [ ] T080 [P] [US4] Prueba Jest en `tecnologia/frontend/tests/paginas/Acta.test.tsx`: las diferencias se resaltan; el resultado ALTERADA se muestra como alerta; INTEGRA se muestra como éxito (Día 4)

**Checkpoint**: flujo completo de punta a punta por API (Día 3) y desde la web (Día 4).

---

## Phase 7: User Story 5 — Seguir la línea de tiempo (Priority: P2) · Día 3

**Goal**: cada usuario ve la línea de tiempo de sus solicitudes con quién, en qué órgano, cuándo y desde qué estado (FR-026 a FR-028).

**Independent Test**: después del flujo completo, `GET /historial` devuelve los pasos en orden, cada uno con usuario, órgano, fecha y estado anterior.

### Tests for User Story 5

- [ ] T081 [P] [US5] Prueba EQ-08 (adaptada a 001) en `tecnologia/backend/tests/integracion/test_eq08_trazabilidad.py`:
  - Recorre el flujo: envío, visto bueno, conformidad, aprobación, despacho y acta.
  - Comprueba que `/historial` muestra los 6 pasos en orden y que la consulta SQL confirma usuario, rol, órgano y fecha en el 100 % de ellos.
  - Comprueba que la cadena de `registro_auditoria` está íntegra, recalculando `data-model.md registro_auditoria.huella`.
  - Comprueba que no hay ningún endpoint para borrar o editar el historial.
  - El resultado se guarda en `evidencias/EQ-08/`.
- [ ] T082 [P] [US5] Prueba Jest en `tecnologia/frontend/tests/componentes/LineaTiempo.test.tsx`: muestra las entradas en orden con sus etiquetas, y el motivo cuando existe

### Implementation for User Story 5

- [ ] T083 [US5] Implementar `tecnologia/backend/app/modules/requests/aplicacion/consultar_historial.py` y `GET /api/v1/requerimientos/{id}/historial` en `.../requests/presentacion/router.py`, con la misma política de acceso de T045
- [ ] T084 [US5] Implementar `tecnologia/frontend/src/componentes/LineaTiempo.tsx` e integrarlo en `tecnologia/frontend/src/paginas/DetalleSolicitud.tsx`

**Checkpoint**: trazabilidad completa visible y comprobada.

---

## Phase 8: User Story 6 — Anular con justificación (Priority: P3) · Día 4

**Goal**: el oficial anula con motivo una solicitud en BORRADOR, por ejemplo una de material de guerra bloqueada; en cualquier otro estado se rechaza (FR-022).

**Independent Test**: `oficial.bim11` anula con motivo una solicitud en BORRADOR, que pasa a ANULADA con el motivo en el historial. Desde cualquier otro estado la respuesta es 409.

### Tests for User Story 6

- [ ] T085 [P] [US6] Prueba de integración en `tecnologia/backend/tests/integracion/test_anulacion.py` con los escenarios 1 a 4 de la US6: anular desde BORRADOR con motivo; sin motivo → 422; desde los demás estados → 409; otra unidad u otro rol → 403 o 404
- [ ] T086 [P] [US6] Prueba Jest en `tecnologia/frontend/tests/paginas/Anular.test.tsx`: el botón solo aparece en BORRADOR y el motivo es obligatorio

### Implementation for User Story 6

- [ ] T087 [US6] Implementar `tecnologia/backend/app/modules/requests/aplicacion/anular_requerimiento.py` y `POST /api/v1/requerimientos/{id}/anular` en `.../requests/presentacion/router.py`, con la transición BORRADOR → ANULADA y `data-model.md historial_requerimiento.motivo` obligatorio
- [ ] T088 [US6] Agregar el botón **Anular**, con un diálogo para el motivo, en `tecnologia/frontend/src/paginas/DetalleSolicitud.tsx`

**Checkpoint**: las 6 historias funcionan.

---

## Phase 9: Polish, pruebas externas y evidencias · Día 4

**Purpose**: pruebas de API y de carga, cobertura, evidencias y ensayo de la demo.

- [ ] T089 [P] Crear `tecnologia/pruebas/postman/sga-001.postman_collection.json` y `local.postman_environment.json` (research §13):
  - Inicio de sesión de cada rol, guardando el token en variables.
  - El flujo completo: registrar, enviar, visto bueno, conformidad, aprobación, despacho, acta y verificación.
  - Los casos 401, 403 y 404 (EQ-01).
  - Los conflictos 409: NIVEL_YA_FIRMADO, STOCK_INSUFICIENTE y REQUIERE_COLOGE.

  Cada petición lleva su `pm.test`. Sirve también como demo de respaldo.
- [ ] T090 Ejecutar la colección con `npx newman run … -r cli,htmlextra` contra Docker Compose y guardar el reporte en `evidencias/EQ-01/` y `evidencias/EQ-08/`
- [ ] T091 [P] Crear `tecnologia/pruebas/k6/eq04_rendimiento.js` (EQ-04, valida el listado, el detalle y el registro de US1 y US5):
  - 20 VU constantes durante 5 min, con la mezcla 60 % `GET /requerimientos`, 30 % `GET /requerimientos/{id}` y 10 % `POST /requerimientos`.
  - `setup()` inicia sesión.
  - Los umbrales son `http_req_duration: ['p(95)<2000']` y `http_req_failed: ['rate<0.01']` (research §11).
- [ ] T092 Ejecutar una corrida de referencia de T091 con `k6 run --summary-export evidencias/EQ-04/k6-resumen-001.json` contra Docker Compose. Repetirla con `CATALOGO_CACHE_ACTIVA=false` y guardar `evidencias/EQ-04/k6-resumen-001-sin-cache.json`, para comparar los p95 con y sin caché (principio VIII). Es opcional en 001: si falta tiempo, pasa a 002
- [ ] T093 [P] Crear `tecnologia/pruebas/k6/eq09_escalabilidad.js` (40 VU, misma mezcla) y `tecnologia/pruebas/k6/estres_2000.js` (`ramping-vus` con escalones 50 → 200 → 500 → 1 000 → 2 000 VU, registrando p95, tasa de errores y punto de quiebre). Solo se escriben los scripts; se ejecutan en el incremento 002, que forma parte del Sprint 2 y es donde se cumple el estrés obligatorio del principio VII
- [ ] T094 Comprobar la cobertura: pytest ≥ 60 % en `requests`, `rules`, `signing` e `inventory`, Jest ≥ 60 % en `src/logica`, `src/auth` y `src/api`, y 0 errores de Ruff y ESLint. Copiar los reportes (`htmlcov/`, `coverage/lcov-report/`) a `evidencias/EQ-07/`
- [ ] T095 [P] Revisar el diseño responsive y la accesibilidad básica en `tecnologia/frontend/src/estilos.css` y en las páginas: etiquetas en todos los campos, foco visible, contraste y vista en un ancho de 360 px. La medición formal con Lighthouse queda para 002 (EQ-05)
- [ ] T096 Ensayar de principio a fin la demo de `specs/001-flujo-solicitud/quickstart.md` (pasos 1 a 10), con la ruta de respaldo por Swagger (`/docs`) y Postman, y corregir lo que falle. Cronometrar el trabajo acumulado del flujo completo, del registro al acta firmada (SC-009: menos de 10 min), y guardar el tiempo de cada paso en `evidencias/SC-009/`
- [ ] T097 [P] Actualizar la sección "Estado del proyecto" y agregar "Cómo ejecutar" en `README.md`, con un enlace a `quickstart.md`. `docs/` no se modifica

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sin dependencias.
- **Foundational (Fase 2)**: depende de Setup y **bloquea todas las historias**.
- **US1 a US6 (Fases 3 a 8)**: dependen de Foundational. Siguen el orden del flujo, porque cada estado nace del anterior:
  - **US1** no depende de ninguna otra historia.
  - **US2** necesita solicitudes enviadas (US1, o los fixtures de la prueba).
  - **US3** necesita una solicitud en PENDIENTE_APROBACION. Usa `firmar_requerimiento` de US2 para el nivel del almacén.
  - **US4** necesita una solicitud EN_TRANSITO (US3) y el servicio de firma de US2. T098 amplía la matriz de T057 (US2) con los endpoints de US3 y US4.
  - **US5** solo lee el historial, que se escribe desde Foundational. Su prueba EQ-08 necesita US1 a US4.
  - **US6** solo depende de US1.
- **Polish (Fase 9)**: depende de US1 a US4. Postman y k6 necesitan el flujo completo.

### Within Each User Story

- Las pruebas [P] se escriben primero y fallan antes de implementar.
- Orden de trabajo: dominio y puertos → casos de uso → router → página del frontend → prueba Jest.
- Para que cada historia se pueda probar sola, sus pruebas de integración preparan el estado inicial con fixtures, sin depender de que otra historia esté terminada.

### Parallel Opportunities

- **Setup**: T003, T004, T005, T006, T007 y T009, después de T001 y T002.
- **Foundational**: los modelos T015 a T020; T024; T027; T031, T032 y T033 junto con T030; el frontend base (T036, T037, T039, T040 y T041) junto con el backend.
- **US1**: T042 y T043 (pruebas), y T050 mientras se hacen T044 a T049.
- **US2**: T055, T056 y T059, y T065 junto con T063 y T064.
- **US3 y US4**: T066, T067, T074 y T075 se pueden escribir a la vez; T098 va después de T057. T072 es independiente de T071.
- **Polish**: T089, T091, T093, T095 y T097.

---

## Parallel Example: User Story 2

```bash
# Pruebas y adaptador de firma a la vez (archivos distintos):
Task: "T055 Prueba unitaria de firma en tecnologia/backend/tests/unitarias/test_firma.py"
Task: "T056 Prueba del conducto regular en tecnologia/backend/tests/integracion/test_conducto_regular.py"
Task: "T059 FirmadorEd25519 en tecnologia/backend/app/modules/signing/infraestructura/firmador_ed25519.py"

# Frontend de US2 mientras el backend de US3 avanza (Día 3):
Task: "T063 Bandeja en tecnologia/frontend/src/paginas/Bandeja.tsx"
Task: "T068 Servicio de despacho en tecnologia/backend/app/modules/inventory/aplicacion/servicio_despacho.py"
```

---

## Calendario por día

| Día | Backend | Frontend | Pruebas | Demostrable al final del día |
|---|---|---|---|---|
| **1 (lunes)** | T001–T004, T008, T010–T031, T034 | T005–T007 (incluye la base de Jest) | T009 (CI), T032, T033, T035 | Inicio de sesión y catálogo por Swagger; CI en verde |
| **2 (martes)** | T044–T049, T058–T062 | T036–T039, T050–T053 | T040–T043, T054, T055–T057 (EQ-01, envío y firmas) | Registrar y enviar desde la web; firmar por Swagger |
| **3 (miércoles)** | T068–T070, T076–T078, T083 | T063, T064, T084 | T065, T066, T067 (EQ-03), T074, T075 (EQ-02), T098 (EQ-01, despacho y acta), T081 (EQ-08), T082 | Todo el conducto regular desde la web; **flujo completo por API** |
| **4 (jueves, demo)** | T087, correcciones | T071, T072, T079, T088, T095 | T073, T080, T085, T086, T089–T094 (Postman, k6, cobertura) | **Flujo completo desde la web**; quickstart ensayado (T096); evidencias |

**Ruta crítica para el jueves**: T001–T035 → T044–T049 → T058–T062 → T068–T070 → T076–T078. Con
esto el **flujo completo es demostrable por Swagger desde el Día 3**, y el frontend del Día 4 es
la mejora visible, no un requisito de la demo.

**Si falta tiempo**, se recorta en este orden, según el plan: T072 (stock, se ve por Swagger),
la edición de un borrador dentro de T046, el filtro por estado de T063 y T092 (corrida k6, pasa a
002). US6 (T085–T088) puede pasar a 002 sin afectar el flujo principal.

---

## Implementation Strategy

### MVP First

1. Fases 1 y 2 (Día 1), con el dominio probado y el CI en verde.
2. US1 (Día 2): **validar** registrar y enviar, incluido el bloqueo del COLOGE.
3. US2 (Día 2–3): **validar** el conducto regular y EQ-01.
4. US3 y US4 (Día 3): **validar** EQ-02, EQ-03 y el flujo completo por API. A partir de aquí el MVP ya se puede demostrar.
5. US5 (Día 3): **validar** EQ-08.
6. Frontend de US3 y US4, US6 y Polish (Día 4): demo desde la web y evidencias.

### Incremental Delivery

Cada historia termina con su checkpoint en verde (pytest y Jest) y se confirma con un commit
convencional, por ejemplo `feat(requests): registrar y enviar requerimientos (US1)` o
`test(inventory): concurrencia de despachos EQ-03`. Así, el flujo principal funciona y se puede
mostrar al cerrar cualquier día.

### Pendiente para el incremento 002 (fuera de este tasks.md)

Nivel del COLOGE y aprobación automática; verificación de la cadena por el auditor; ejecución de
k6 para EQ-04 (formal), EQ-09 y estrés de 2 000 VU; Lighthouse (EQ-05); Uptime Kuma y
`docker kill` (EQ-06); prueba de cambio de regla de EQ-07. El incremento 002 forma parte del
Sprint 2 y **debe cerrar** las dos desviaciones temporales de la constitución v1.2.0: el PDF
verificable de cada firma y del acta (DT-01) y HTTPS junto con el despliegue (DT-02).
