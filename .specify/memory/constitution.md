<!--
Informe de impacto de sincronización (Sync Impact Report)
- Cambio de versión: 1.2.0 → 1.3.0 (MINOR).
  Motivo: se cierra la desviación temporal DT-01 (el PDF verificable ya es obligatorio y está
  implementado en 002), se prorroga DT-02 (HTTPS) por decisión de la autora y se fija el término
  del resultado de verificar un PDF. Cambia materialmente lo que se acepta como cumplimiento de los
  principios IX y X; ningún principio se elimina ni se redefine, así que no es MAJOR.
- Enmienda por decisión de la autora (2026-11-24). `docs/` no se modifica.
- Principios modificados:
  IX. Reglas de dominio: ya no remite a DT-01; el PDF verificable rige plenamente. La verificación
      de un PDF responde AUTENTICO o ALTERADO (literal a EQ-02); la de firmas conserva INTEGRA o
      ALTERADA.
  X. Actores y seguridad: DT-02 sigue vigente después de 002, con cierre obligatorio en el
     Sprint 2.
- Secciones modificadas: "Conflictos con docs/ y su resolución" (DT-01 cerrada, DT-02 prorrogada,
  fila nueva DV-10 y término del resultado); "Flujo de desarrollo y puertas de calidad".
- Secciones añadidas: ninguna. Secciones eliminadas: ninguna.
- Plantillas dependientes: no se modifican; leen la constitución en tiempo de ejecución.
- Artefactos afectados: specs/002-documento-firmado/plan.md ya cita esta enmienda (DV-10, DT-01 y
  DT-02). La descripción del endpoint de verificación de 001 que menciona DT-01 se actualiza en la
  tarea T043 de 002.
- Por revisar: nada. El término ALTERADO/ALTERADA queda resuelto.
- Pendientes: ninguno con marcador TODO.
-->

# Constitución del SGA — Sistema de Gestión de Almacén con Firma Digital

Proyecto académico del curso IS488 Arquitectura de Software (UNSCH), orientado a la logística del
Ejército del Perú. Rige el **Sprint 2: "Implementación y validación de la arquitectura"** y todas
las especificaciones, planes, tareas e implementaciones del repositorio, desarrolladas con
Spec-Driven Development (SDD).

## Core Principles

### I. Fidelidad a la arquitectura documentada (NO NEGOCIABLE)

- La carpeta `docs/` (Sprint 1) es la **fuente de verdad** del proyecto. La implementación DEBE
  respetar su estilo arquitectónico (monolito modular + capas, ADR-001), su enfoque (Clean
  Architecture dentro de cada módulo, ADR-002), sus componentes (los ocho módulos y la
  infraestructura del C4), su stack y sus decisiones (ADR-001 a ADR-013).
- **Stack obligatorio** (ADR-011 y C4 nivel 2): backend **Python + FastAPI** (SQLAlchemy,
  Pydantic, `cryptography`, ReportLab), frontend **React + TypeScript**, base de datos
  **PostgreSQL**, balanceador **Nginx**, monitoreo **Uptime Kuma** y despliegue con **Docker
  Compose**.
- `docs/` es de **solo lectura** para el flujo SDD: ningún comando de Spec Kit la crea, modifica ni
  elimina. Los artefactos SDD (especificación, plan, tareas, contratos) se guardan en `specs/`.
- Si una especificación, plan, tarea o esta misma constitución contradice `docs/`, **prevalece
  `docs/`**. Todo conflicto DEBE reportarse explícitamente (en la sección de complejidad del plan
  o en "Conflictos con docs/ y su resolución"); nunca se resuelve en silencio.
- Una desviación de `docs/` solo es válida si la aprueba la autora y queda registrada en
  "Conflictos con docs/ y su resolución", con su motivo y su alcance. Así se cambia la forma de
  cumplir `docs/` sin reescribirla.

**Justificación:** el Sprint 2 consiste en implementar y validar la arquitectura diseñada en el
Sprint 1; si el código se aparta de ella, la validación pierde sentido.

### II. Especificaciones SDD

- Cada funcionalidad implementada DEBE tener su especificación en `specs/` con historias de
  usuario (trazadas a HU01–HU13 y RF01–RF12 de `docs/`), criterios de aceptación verificables y
  tareas técnicas.
- NO PUEDE escribirse código de una funcionalidad sin su especificación aprobada.

**Justificación:** SDD es una restricción del docente (RC03).

### III. Desarrollo incremental

- Lo desarrolla una sola persona (RC06) en un plazo total de **2 a 3 semanas**, en incrementos
  funcionales. Cada incremento DEBE dejar el sistema funcionando y con sus pruebas en verde.
- El primer incremento (MVP) DEBE funcionar en **5 días** y cubrir de punta a punta el flujo
  principal: **solicitud → aprobación por el conducto regular, incluida la División/Brigada →
  despacho del almacén → acta de recepción firmada**, con los niveles que fija `docs/` para el
  caso normal (ver principio IX y la sección de conflictos).
- Ninguna funcionalidad fuera del incremento en curso PUEDE implementarse "de paso"; se registra
  como pospuesta.

**Justificación:** un flujo completo y demostrable temprano reduce el riesgo del plazo.

### IV. API REST documentada

- Todos los endpoints DEBEN ser REST (RC05) bajo el prefijo `/api/v1` (C4 nivel 3) y estar
  documentados con **OpenAPI/Swagger**, accesible desde el propio servicio (la documentación que
  FastAPI genera, por ejemplo en `/docs`).
- Cada endpoint DEBE declarar sus esquemas de entrada y salida y sus respuestas de error (401,
  403, 404, 409, 422).
- La API DEBE exponer el punto de verificación de estado `/health` (ADR-013).

**Justificación:** la API es el contrato entre el frontend y el backend; documentarla en el propio
servicio la mantiene al día.

### V. Diseño limpio

- Se aplican los principios **SOLID** tal como los documenta
  `docs/03-diseno-de-software/diseno-interno/principios-de-diseno.md`.
- Los patrones de `docs/` son la base: **Repository**, **Adapter**, **State**, **Unit of Work** e
  **Inyección de dependencias** (C4 nivel 4). Otros patrones (por ejemplo Strategy para las
  reglas de aprobación o Factory) PUEDEN aplicarse cuando corresponda, y cada uno DEBE
  justificarse en el plan.
- La regla de dependencia es obligatoria: el dominio no importa FastAPI, SQLAlchemy ni
  `cryptography`; un módulo nunca usa las tablas ni el repositorio de otro, solo sus casos de uso.

**Justificación:** mantenibilidad (AC07) y reglas de negocio que se prueban sin infraestructura.

### VI. Pruebas automatizadas: pytest en el backend y Jest en el frontend (NO NEGOCIABLE)

- **Backend**: las funcionalidades y reglas de negocio DEBEN tener pruebas automatizadas con las
  herramientas de `docs/` (ADR-011): **pytest** (unitarias), **pytest + httpx** (integración de la
  API) y **pytest-cov** (reporte de cobertura), más **Ruff** para el análisis estático. Jest NO
  PUEDE usarse en el backend.
- **Frontend**: la lógica de la interfaz (validaciones de formularios, acciones visibles por rol y
  estado, rutas protegidas, manejo de errores y estados de carga) y sus componentes principales
  DEBEN tener pruebas con **Jest**, con **reporte de cobertura** y un umbral mínimo del **60 %**
  en la lógica, la sesión y el cliente de la API. Lo exige el entregable del Sprint 2.
- Son obligatorias las pruebas de: el conducto regular (ningún nivel se omite ni firma dos veces),
  todas las transiciones de estado válidas e inválidas, y la inmutabilidad y verificación del
  acta firmada (incluido el caso de un documento alterado).
- La cobertura de los módulos críticos (Requerimientos, Reglas, Firma digital e Inventario) DEBE
  ser de **60 % o más**, con 0 errores de Ruff (EQ-07).
- Un pipeline de **GitHub Actions** DEBE ejecutar, en cada push y cada pull request, Ruff y pytest
  con cobertura en el backend, y el lint y Jest con cobertura en el frontend. Un pipeline en rojo
  bloquea la integración, y los reportes de cobertura se publican como artefactos.

**Justificación:** los errores en estas reglas comprometen la integridad del proceso logístico.

### VII. Validación de atributos de calidad

- Cada escenario de `docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md` (EQ-01 a
  EQ-09) DEBE tener una prueba que lo valide, con la herramienta y la medida que define el propio
  escenario: pytest + httpx (EQ-01, EQ-08), pytest + `cryptography` (EQ-02), pytest + PostgreSQL
  (EQ-03), Google Lighthouse (EQ-05), `docker kill` + Uptime Kuma (EQ-06) y regresión + pytest-cov
  + Ruff (EQ-07). Hay una excepción aprobada: para **EQ-04 y EQ-09 se usa k6** en lugar de
  Locust. Se cambia solo la herramienta: el estímulo y las medidas de `docs/` (p95 < 2 s con 20
  usuarios y con 40 usuarios en 2 instancias) siguen siendo el criterio de aceptación.
- DEBE ejecutarse con **k6** una prueba de estrés con carga progresiva hasta **2 000 usuarios
  virtuales concurrentes**, porque la exige el entregable del Sprint 2. Su resultado (p95, tasa de
  errores y punto de quiebre) se reporta, pero no sustituye a los criterios de aceptación de
  EQ-04 y EQ-09.
- Las pruebas de la API desde fuera del proceso DEBEN tener una colección **Postman** versionada,
  ejecutable con **Newman**, que cubra el flujo principal y los casos de rechazo (401, 403, 404,
  409). Complementa a pytest, que sigue siendo la fuente de verdad de la lógica.
- Las evidencias (reportes, capturas, resultados) DEBEN guardarse en el repositorio **fuera de
  `docs/`**, en una carpeta de evidencias por escenario.

**Justificación:** el Sprint 2 valida la arquitectura; un atributo de calidad sin prueba ni
evidencia no está validado.

### VIII. Datos y caché

- El plan de cada incremento DEBE diseñar explícitamente el comportamiento de la base de datos:
  índices de las consultas críticas (bandeja por estado y órgano, línea de tiempo, stock por
  almacén e ítem), paginación de los listados y transacciones con bloqueo del stock (ADR-003).
- El esquema DEBE gestionarse con migraciones versionadas y los datos de prueba con seeds
  ficticios (RC13); la base de datos no se modifica manualmente.
- `docs/` no define una caché. Si el plan propone una, DEBE describir qué consultas se cachean, su
  política de invalidación y su efecto medido en EQ-04. La API DEBE seguir sin guardar estado de
  sesión (ADR-006, ADR-012). Un contenedor nuevo (por ejemplo Redis) es una desviación del C4
  nivel 2 y DEBE reportarse según el principio I.
- Estas decisiones DEBEN validarse con pruebas: EQ-03 (stock igual a la suma de sus movimientos
  con despachos simultáneos) y EQ-04/EQ-09 (rendimiento).

**Justificación:** la consistencia del inventario (AC03) y el rendimiento (AC04) dependen del
diseño de los datos, no solo del código.

### IX. Reglas de dominio

- **Conducto regular:** toda solicitud de una unidad pasa primero por su División o Brigada y
  sigue la máquina de estados de `docs/` (ADR-007): visto bueno del comandante → conformidad de la
  Gran Unidad → autorización del COLOGE (material de guerra o monto alto) → aprobación del jefe de
  almacén → despacho → acta de recepción. Ningún nivel PUEDE omitirse ni firmar dos veces (RN01,
  RN02); cualquier firmante PUEDE rechazar indicando el motivo (RN05); toda transición no listada
  es rechazada por el dominio.
- **Trazabilidad:** cada cambio de estado, firma, rechazo y movimiento DEBE registrarse con
  usuario, órgano, fecha y hora (AC08) en la auditoría encadenada (ADR-005), dentro de la misma
  transacción (RN07).
- **Nada se elimina:** ningún registro de negocio PUEDE borrarse físicamente; solo se anula con
  justificación y en los casos que permite `docs/` (desde BORRADOR; una vez despachado ya no puede
  anularse, RN06). El registro de movimientos no se modifica (RF06).
- **Firma digital:** `docs/` define el mecanismo (ADR-004): huella **SHA-256** firmada con
  **Ed25519** usando la clave del sistema, en cada nivel y en el acta, con PDF verificable. El
  acta de recepción la firma el **oficial de logística de la unidad**; una vez firmada es
  **inmutable** y la verificación DEBE responder ALTERADO ante cualquier cambio (EQ-02). La
  criptografía se usa desde la librería `cryptography`, nunca programada a mano. Cada PDF emitido
  (de cada estado firmado del requerimiento y del acta) se genera con ReportLab, se firma con
  Ed25519 sobre la huella SHA-256 de sus bytes y se guarda sin cambios a través de
  `AlmacenDocumentos` (ADR-010). La verificación de un PDF responde **AUTENTICO** o **ALTERADO**
  (literal a EQ-02, "el documento"); la de las firmas de un requerimiento responde **INTEGRA** o
  **ALTERADA** ("la firma"). La desviación DT-01 quedó cerrada en el incremento 002.
- **Alcance:** solo **intendencia** y **material de guerra**; fuera quedan compras, presupuesto,
  pagos y el SIGA MEF (RC12).

**Justificación:** son las restricciones institucionales (RC09, RC10, RC11) que dan sentido al
sistema.

### X. Actores y seguridad

- Los actores son siempre personas con un rol (los ocho de
  `docs/01-analisis-de-sistema/01-actores.md`); el sistema nunca es un actor y los órganos son
  datos. La aprobación automática (RN04) es una regla configurada (ADR-008), no un actor.
- Toda funcionalidad, salvo el inicio de sesión, DEBE requerir autenticación con **JWT**
  (ADR-006). El acceso se controla por rol y por órgano en el backend, en cada petición, con
  mínimo privilegio: sin sesión 401, sin permiso 403, recurso de otra unidad 404 (EQ-01).
- Las contraseñas DEBEN guardarse con hash seguro y la comunicación DEBE ser por HTTPS (AC01).
  Rige la desviación temporal DT-02 (HTTP solo en el entorno local), prorrogada después del
  incremento 002; ver "Conflictos con docs/ y su resolución". Credenciales, claves de firma y secretos NO PUEDEN
  versionarse; se usan variables de entorno.

**Justificación:** la información logística militar es sensible y cada decisión tiene un
responsable identificable.

### XI. Documentación, código y commits en español

- Especificaciones, planes, tareas, documentación y comentarios del código DEBEN redactarse en
  español. Los nombres de carpetas y archivos van en español sin tildes, como fija el diseño
  interno de `docs/`; las librerías externas conservan sus nombres.
- Los commits DEBEN seguir Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
  `chore:`, `ci:`) con descripción en español.

**Justificación:** el proyecto se evalúa en español y un historial uniforme facilita la revisión.

## Conflictos con docs/ y su resolución

Conflictos detectados entre los pedidos de la autora y `docs/`. Salvo las desviaciones aprobadas
indicadas, se resuelven a favor de `docs/` según el principio I (decisiones de la autora del
2026-11-22):

| Pedido original | Lo que fija `docs/` | Resolución |
|---|---|---|
| Backend Node.js con pruebas en Jest | Python + FastAPI; pytest, httpx, pytest-cov y Ruff (ADR-011, C4, EQ-01/02/03/07/08) | Se usa el stack de `docs/` (principios I y VI) |
| Pruebas de carga con k6 hasta 2 000 VU (entregable del Sprint 2) | Locust con 20 y 40 usuarios, p95 < 2 s (EQ-04, EQ-09) | **Desviación aprobada (v1.1.0)**: se usa k6 y se conservan las medidas de `docs/`; el estrés de 2 000 VU es obligatorio y se reporta aparte (VII) |
| Pruebas del frontend con Jest y cobertura (entregable del Sprint 2) | `docs/` no define pruebas del frontend; el backend usa pytest (ADR-011) | **Ampliación aprobada (v1.1.0)**: Jest solo en el frontend; el backend sigue con pytest (VI) |
| Pruebas de la API con Postman | `docs/` usa pytest + httpx para la API (EQ-01, EQ-08) | **Ampliación aprobada (v1.1.0)**: colección Postman/Newman como complemento; pytest sigue siendo el criterio (VII) |
| Firma del MVP como hash SHA-256 solo | SHA-256 + Ed25519 con PDF verificable (ADR-004) | Ed25519 desde el MVP (IX) |
| Firma del incremento 001 verificada sin PDF | SHA-256 + Ed25519 con PDF verificable (ADR-004, RF05, ADR-010) | **DT-01 cerrada (v1.3.0)**: el incremento 002 emite el PDF verificable de cada estado firmado y del acta (IX) |
| Entorno local por HTTP | Comunicación por HTTPS (AC01) | **Desviación temporal aprobada DT-02 (v1.2.0, prorrogada en v1.3.0)**: el entorno local sigue en HTTP después de 002; HTTPS se implementa junto con el despliegue, con cierre obligatorio dentro del Sprint 2 (X) |
| Resultado de la verificación: ALTERADO (EQ-02) frente a ALTERADA (specs de 001) | EQ-02: "el sistema indica que fue alterado" (ALTERADO) | **Resuelto (v1.3.0)**: un PDF se verifica como AUTENTICO/ALTERADO; las firmas de un requerimiento, como INTEGRA/ALTERADA. Ambas detectan el 100 % de las alteraciones (IX) |
| Ubicación de `almacen_documentos_disco.py` | El diseño interno lo pone en `requests/infraestructura/`; el C4 nivel 3 asigna "generación del PDF y verificación" a Firma digital (`modules/signing/`) | **Conflicto entre documentos de `docs/` resuelto a favor del C4 (DV-10, v1.3.0)**: el puerto y el adaptador viven en `signing`; el archivo conserva su nombre y la generación con ReportLab va en un adaptador propio (V) |
| MVP: solicitud → División/Brigada → despacho → acta | Ningún nivel puede omitirse (RN02): incluye comandante y jefe de almacén | El MVP incluye esos niveles (ver abajo) |
| Estrategia de caché obligatoria | Sin caché en la arquitectura | El plan la propone y reporta cualquier componente nuevo (VIII) |
| Código en `tecnologia/` (README) | Estructura `backend/app/modules/...` (diseño interno) | Se respeta la estructura interna de `docs/`; su ubicación en el repositorio se fija en el plan |

**Alcance del MVP compatible con RN02:** visto bueno del comandante → conformidad de la
División/Brigada → aprobación del jefe de almacén → despacho del almacenero → acta firmada por el
oficial de logística. La autorización del COLOGE y la aprobación automática (RN03, RN04) son
caminos condicionales y llegan en un incremento posterior. Mientras tanto, el MVP DEBE rechazar
las solicitudes que requieran autorización del COLOGE en lugar de omitir ese nivel, y las de bajo
riesgo pasan por la aprobación manual del jefe de almacén. Ambas son desviaciones temporales que el
plan del MVP DEBE declarar.

**Desviaciones temporales (DT-01 y DT-02):** se aprobaron para el incremento 001 (v1.2.0).
**DT-01 quedó cerrada en el incremento 002 (v1.3.0).** **DT-02 se prorroga** por decisión de la
autora del 2026-11-24 (v1.3.0): sigue vigente después de 002 y su cierre es **obligatorio dentro
del Sprint 2**; no PUEDE prorrogarse otra vez sin una nueva enmienda. Historial y reglas:

- **DT-01 (principio IX), cerrada:** en 001 la firma Ed25519 sobre la huella SHA-256 se aplicaba
  igual en cada nivel y en el acta; solo faltaba el PDF. El endpoint de verificación DEBE responder INTEGRA o ALTERADA y
  sus pruebas (incluido el documento alterado, EQ-02) son obligatorias desde 001. En 002 se genera
  el PDF verificable de cada firma y del acta (RF05, ADR-010).
- **DT-02 (principio X / AC01):** HTTP se admite solo en el entorno local de desarrollo y de la
  demo; ningún despliegue fuera de ese entorno PUEDE usar HTTP. Las demás medidas de seguridad del
  principio X (JWT, control por rol y órgano, hash de contraseñas, secretos fuera del repositorio)
  rigen desde 001. HTTPS se configura junto con el despliegue, en un incremento posterior a 002
  dentro del Sprint 2.
- El plan y las tareas de 001 declararon ambas desviaciones; el plan de 002 incluye las tareas que
  cierran DT-01, y el plan del incremento que configure el despliegue DEBE incluir las que cierran
  DT-02.

## Flujo de desarrollo y puertas de calidad

- Por cada incremento: `/speckit-specify` → `/speckit-clarify` (si hay ambigüedades) →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`.
- Cada plan DEBE incluir la revisión de cumplimiento de esta constitución ("Constitution Check")
  y comparar sus decisiones con `docs/`; toda desviación DEBE justificarse en la sección de
  complejidad del plan.
- Un incremento está terminado cuando: cumple su especificación, el flujo principal sigue
  funcionando, el pipeline de GitHub Actions está en verde (VI), los escenarios de calidad que
  afecta tienen prueba y evidencia (VII) y los cambios están en commits convencionales (XI).
- El incremento 002 no está terminado mientras siga abierta la desviación temporal DT-01 (PDF
  verificable). El Sprint 2 no está terminado mientras siga abierta DT-02 (HTTPS).

## Governance

- Esta constitución prevalece sobre cualquier otra práctica o plantilla del repositorio, excepto
  sobre `docs/`, que prevalece sobre ella (principio I).
- **Cambios en `docs/`:** solo los hace la autora a mano, fuera del flujo SDD, en un commit
  `docs:` propio. Si el cambio afecta un principio o la tabla de conflictos, la constitución DEBE
  enmendarse en consecuencia.
- **Procedimiento de enmienda:** toda modificación se hace con `/speckit-constitution`, describe
  el cambio y su motivo, actualiza la versión y la fecha de última enmienda, y se registra en un
  commit `docs:` propio (por ejemplo, `docs: enmendar constitución a v1.2.0 (...)`). Las
  especificaciones y planes afectados DEBEN revisarse.
- **Versionado semántico:**
  - **MAJOR**: se elimina o redefine un principio de forma incompatible con el trabajo previo.
  - **MINOR**: se añade un principio o sección, o se amplía materialmente una guía existente.
  - **PATCH**: aclaraciones, redacción o correcciones sin cambio de significado.
- **Revisión de cumplimiento:** cada plan y cada cierre de incremento verifican el cumplimiento de
  los principios; los incumplimientos se corrigen o se justifican explícitamente.

**Version**: 1.3.0 | **Ratified**: 2026-11-22 | **Last Amended**: 2026-11-24
