# Tasks: Documento firmado y PDF verificable (incremento 002)

**Input**: documentos de diseño en `specs/002-documento-firmado/` (plan.md, spec.md, research.md,
data-model.md, contracts/openapi.yaml, quickstart.md)

**Tests**: obligatorios por la constitución (principio VI): pytest en el backend y Jest en el
frontend. En cada historia, las pruebas se escriben primero y deben fallar antes de implementar.

**Organización**: por historia de usuario; cada fase deja el sistema funcionando y en verde. Al
cerrar cada fase: Ruff, pytest, ESLint, `tsc` y Jest; `docker compose up --build -d`; una prueba
rápida con curl; marcar [X]; commit convencional y `git push`.

Rutas: `B/` = `tecnologia/backend/`, `F/` = `tecnologia/frontend/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede hacerse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de spec.md (US1…US5)

---

## Phase 1: Setup

- [ ] T001 Agregar `reportlab>=4.2` a las dependencias de `B/pyproject.toml` e instalarla en el entorno local
- [ ] T002 [P] Agregar `documentos_dir` (por defecto `/datos/documentos`) y `pdf_tamano_maximo` (5 MB) a `B/app/core/config.py`, y `DOCUMENTOS_DIR`/`PDF_TAMANO_MAXIMO` sin secretos a `tecnologia/.env.example`
- [ ] T003 [P] Montar el volumen `documentos` en `/datos/documentos` del servicio `api` en `tecnologia/docker-compose.yml`, y crear esa carpeta con dueño `sga` antes de `USER sga` en `B/Dockerfile` (research §7)
- [ ] T004 [P] Agregar `client_max_body_size 6m;` a `location /api/` en `tecnologia/nginx/default.conf` (research §6)
- [ ] T005 Crear la migración `B/migrations/versions/0003_documento_emitido.py` con la tabla, los índices únicos y el disparador de inmutabilidad de `data-model.md`, columna por columna: `documento_emitido.id`, `documento_emitido.codigo_verificacion`, `documento_emitido.tipo`, `documento_emitido.requerimiento_id`, `documento_emitido.ultima_firma_id`, `documento_emitido.firmas_incluidas`, `documento_emitido.huella_contenido`, `documento_emitido.huella_sha256`, `documento_emitido.firma`, `documento_emitido.metodo`, `documento_emitido.clave_id`, `documento_emitido.clave_almacen`, `documento_emitido.tamano_bytes`, `documento_emitido.emitido_por`, `documento_emitido.organo_id` y `documento_emitido.emitido_en`, y su modelo `DocumentoEmitidoModelo` en `B/app/modules/signing/infraestructura/modelos.py`

---

## Phase 2: Foundational (bloquea US1–US5)

- [ ] T006 [P] Prueba unitaria del dominio de documentos en `B/tests/unitarias/test_documento.py`: `generar_codigo()` cumple el formato de `data-model.md` `documento_emitido.codigo_verificacion`, `extraer_codigo(bytes)` lo encuentra o devuelve None, y `huella_contenido()` es estable y cambia si cambia una cantidad
- [ ] T007 Crear `B/app/modules/signing/dominio/documento.py` (Python puro): `TipoDocumento`, `SelloDocumento`, `LineaDocumento`, `DocumentoPdf` con `contenido_canonico()`/`huella_contenido()`, `DocumentoEmitido`, `generar_codigo()` y `extraer_codigo()` (research §2 y §3); agregar `ResultadoPdf` (AUTENTICO, ALTERADO) a `B/app/modules/signing/dominio/tipos.py` y los errores `DocumentoExistente`/`DocumentoNoEncontrado` a `B/app/modules/signing/dominio/errores.py`
- [ ] T008 Agregar los puertos `AlmacenDocumentos`, `GeneradorPdf` y `RepositorioDocumentos` a `B/app/modules/signing/dominio/puertos.py` (data-model.md, "Puertos nuevos")
- [ ] T009 [P] Prueba unitaria del adaptador de disco en `B/tests/unitarias/test_almacen_documentos_disco.py` (con `tmp_path`): guarda y lee, se niega a sobrescribir, rechaza claves con `..` o absolutas, y lee lo que no existe → `DocumentoNoEncontrado`
- [ ] T010 [P] Implementar `AlmacenDocumentosDisco` en `B/app/modules/signing/infraestructura/almacen_documentos_disco.py` (ADR-010, research §7: escritura exclusiva y atómica, sin método de borrado)
- [ ] T011 [P] Prueba unitaria del generador en `B/tests/unitarias/test_generador_pdf.py`: los bytes empiezan con `%PDF-`, contienen el código en los metadatos (`extraer_codigo` lo encuentra) y se generan con muchos ítems (varias páginas)
- [ ] T012 [P] Implementar `GeneradorPdfReportLab` en `B/app/modules/signing/infraestructura/generador_pdf_reportlab.py` (research §8: A4, encabezado, tabla de ítems, sellos, huella del contenido, pie con código y página, sin logos oficiales; hora de Perú)
- [ ] T013 Implementar `RepositorioDocumentosPostgres` en `B/app/modules/signing/infraestructura/repositorio_documentos_postgres.py` (convierte el `IntegrityError` del índice único en `DocumentoExistente` con un savepoint)
- [ ] T014 Registrar los adaptadores en `B/app/modules/signing/infraestructura/dependencias.py` (`obtener_almacen_documentos()`, `obtener_generador_pdf()`) y extender la prueba de reglas de dependencia `B/tests/unitarias/test_reglas_dependencia.py` para que el dominio y la aplicación de `signing` no importen `reportlab` ni `os`/`pathlib`

**Checkpoint**: puertos y adaptadores probados; ninguna ruta nueva todavía.

---

## Phase 3: User Story 1 - Ver el requerimiento como documento oficial (P1) 🎯 MVP

**Goal**: el detalle muestra el documento oficial con encabezado, ítems y sellos.

**Independent Test**: una solicitud con dos firmas muestra el encabezado completo, los ítems y dos sellos con todos sus datos; un usuario de otra unidad recibe 404.

- [ ] T015 [P] [US1] Prueba de integración en `B/tests/integracion/test_documentos.py`: `GET /requerimientos/{id}/documento` → 200 con encabezado, ítems y sellos en orden (incluido un rechazo con su motivo), sin el sello del acta; 401 sin sesión; 404 para otra unidad
- [ ] T016 [US1] Crear `B/app/modules/requests/aplicacion/consultar_documento.py`: `ConsultarDocumento` aplica `cargar_visible`, arma `DocumentoPdf` (tipo REQUERIMIENTO o ACTA) con el catálogo, las firmas y los motivos de la línea de tiempo (data-model.md, "Qué incluye cada documento"); devuelve también `pdf_disponible`
- [ ] T017 [US1] Agregar `DocumentoSalida` y `SelloSalida` a `B/app/modules/requests/presentacion/esquemas.py`, la ruta `GET /{id}/documento` a `B/app/modules/requests/presentacion/router.py` y su construcción en `B/app/modules/requests/infraestructura/dependencias.py` (contrato `Documento`)
- [ ] T018 [P] [US1] Prueba Jest `F/tests/componentes/DocumentoOficial.test.tsx`: encabezado (SGA, número, unidad, Gran Unidad, almacén, fecha), tabla de ítems, un sello por firma con nivel, decisión, cargo, órgano, fecha, hora, método y huella abreviada, y el texto "Todavía no hay firmas."
- [ ] T019 [US1] Agregar los tipos `Documento`/`Sello` a `F/src/api/tipos.ts` y `obtenerDocumento(id)` a `F/src/api/cliente.ts`, con su prueba en `F/tests/api/cliente.test.ts`
- [ ] T020 [US1] Crear `F/src/componentes/DocumentoOficial.tsx` (reutiliza `huellaAbreviada`, `fechaHora` y las etiquetas de nivel; estilos `.documento` en `F/src/estilos.css`, legibles en celular) y mostrarlo en la sección "Documento" de `F/src/paginas/DetalleSolicitud.tsx`, actualizando `F/tests/paginas/DetalleSolicitud.test.tsx`

**Checkpoint**: US1 funciona sola.

---

## Phase 4: User Story 2 - Revisar el documento antes de firmar (P1)

**Goal**: no se firma ni se rechaza sin "He revisado el documento".

**Independent Test**: el botón de firmar queda deshabilitado hasta marcar la casilla; la API rechaza con 422 una firma sin `documento_revisado`.

- [ ] T021 [P] [US2] Prueba de integración en `B/tests/integracion/test_documentos.py`: `POST /{id}/firmas` sin `documento_revisado` o con `false` → 422 y ninguna firma registrada; con `true` → 201
- [ ] T022 [US2] Agregar `documento_revisado: bool` obligatorio (validado como `true`) a `DecisionFirmaEntrada` en `B/app/modules/requests/presentacion/esquemas.py` (research §9) y actualizar los cuerpos de firma de las pruebas de 001 en `B/tests/integracion/apoyo.py` y donde se firme directamente
- [ ] T023 [P] [US2] Actualizar `tecnologia/pruebas/postman/sga-001.postman_collection.json` para enviar `documento_revisado: true` en cada firma y agregar un caso 422 sin el campo
- [ ] T024 [P] [US2] Prueba Jest `F/tests/paginas/DetalleSolicitud.test.tsx`: al abrir firmar y rechazar se ve el documento; "Sí, firmar" y "Confirmar rechazo" están deshabilitados hasta marcar "He revisado el documento"; el cuerpo enviado lleva `documento_revisado: true`
- [ ] T025 [US2] Crear `F/src/componentes/CasillaRevision.tsx` y usarla junto a `DocumentoOficial` dentro de `DialogoConfirmacion` (firmar) y `DialogoMotivo` (rechazar) en `F/src/paginas/DetalleSolicitud.tsx`; agregar `documento_revisado` al cuerpo de firma en `F/src/api/cliente.ts` (sin `window.confirm` ni `alert`)

**Checkpoint**: US1 y US2 funcionan.

---

## Phase 5: User Story 3 - Descargar el PDF con código de verificación (P1)

**Goal**: el PDF del requerimiento se emite una vez por estado firmado, firmado con Ed25519 y guardado sin cambios.

**Independent Test**: dos descargas sin firmas nuevas devuelven los mismos bytes y el mismo código; tras una firma nueva el código cambia y el PDF anterior se conserva.

- [ ] T026 [P] [US3] Prueba unitaria `B/tests/unitarias/test_emitir_documento.py` con dobles de los tres puertos y `FirmadorFalso`: emite (genera, firma la huella de los bytes, guarda archivo y fila); reutiliza el ya emitido; ante `DocumentoExistente` concurrente devuelve el existente; si el archivo leído no coincide con su huella lanza `Conflicto` (FR-013)
- [ ] T027 [US3] Implementar `EmitirDocumento` en `B/app/modules/signing/aplicacion/emitir_documento.py` (research §4; completa los campos de `data-model.md` `documento_emitido.huella_contenido`, `documento_emitido.huella_sha256`, `documento_emitido.firma`, `documento_emitido.metodo`, `documento_emitido.clave_id`, `documento_emitido.clave_almacen`, `documento_emitido.firmas_incluidas`, `documento_emitido.emitido_por`, `documento_emitido.organo_id` y `documento_emitido.emitido_en`) y construirlo con `construir_emitir_documento(sesion)` en `B/app/modules/signing/infraestructura/dependencias.py`
- [ ] T028 [P] [US3] Prueba de integración en `B/tests/integracion/test_documentos.py`: `GET /{id}/documento.pdf` → 200 `application/pdf` con `X-Codigo-Verificacion`; dos descargas → bytes idénticos; firma nueva → código nuevo y el anterior sigue en el almacenamiento; sin firmas → 409; otra unidad → 404; sin sesión → 401. Las firmas se hacen con el flujo de 001 antes de la primera descarga, lo que cubre FR-015
- [ ] T029 [US3] Crear `B/app/modules/requests/aplicacion/descargar_pdf.py` (`DescargarPdf`: visibilidad, `ConsultarDocumento`, sin firmas → `Conflicto`, llama a `EmitirDocumento`) y la ruta `GET /{id}/documento.pdf` con `Content-Disposition` en `B/app/modules/requests/presentacion/router.py`
- [ ] T030 [P] [US3] Agregar `descargarPdf(ruta, nombre)` a `F/src/api/cliente.ts` (pide el blob con el token y lo guarda con un enlace temporal y `URL.createObjectURL`) con su prueba en `F/tests/api/cliente.test.ts`
- [ ] T031 [US3] Botón "Descargar PDF" (ícono `FileDown`) en la sección "Documento" de `F/src/paginas/DetalleSolicitud.tsx`, visible si `pdf_disponible`, con mensaje de error accesible; prueba en `F/tests/paginas/DetalleSolicitud.test.tsx`

**Checkpoint**: US1–US3 funcionan.

---

## Phase 6: User Story 4 - Documento y PDF del acta de recepción (P1)

**Goal**: el acta tiene su propio documento y PDF con lo despachado, lo recibido y las observaciones.

**Independent Test**: una solicitud "Recibida" con una diferencia muestra el acta y descarga su PDF con un código distinto del PDF del requerimiento.

- [ ] T032 [P] [US4] Prueba de integración en `B/tests/integracion/test_documentos.py`: `GET /{id}/acta/documento` → líneas con despachado, recibido y observación, `tiene_diferencias` y el sello del acta; `GET /{id}/acta/documento.pdf` → PDF con un código propio (distinto del requerimiento), y firmar el acta no cambia el PDF del requerimiento; sin acta → 404
- [ ] T033 [US4] Soporte del tipo ACTA en `ConsultarDocumento` y `DescargarPdf` (líneas con despachado, recibido y observación, `tiene_diferencias`, sello `ACTA_RECEPCION`) y las rutas `GET /{id}/acta/documento` (JSON, contrato `Documento` con `tipo` ACTA) y `GET /{id}/acta/documento.pdf` en `B/app/modules/requests/presentacion/router.py`; el generador imprime las columnas del acta en `B/app/modules/signing/infraestructura/generador_pdf_reportlab.py`
- [ ] T034 [P] [US4] Prueba Jest en `F/tests/paginas/Acta.test.tsx`: la sección del acta muestra su documento (`DocumentoOficial` con las columnas del acta) y el botón "Descargar PDF del acta" y lo llama con la ruta del acta
- [ ] T035 [US4] Agregar `obtenerDocumentoActa(id)` a `F/src/api/cliente.ts`, soportar las columnas del acta en `F/src/componentes/DocumentoOficial.tsx` y mostrar el documento del acta con el botón "Descargar PDF del acta" en `F/src/paginas/DetalleSolicitud.tsx`

**Checkpoint**: US1–US4 funcionan.

---

## Phase 7: User Story 5 - Verificar un PDF subido (P1)

**Goal**: el sistema dice si un PDF es AUTENTICO o ALTERADO (EQ-02).

**Independent Test**: el PDF descargado tal cual → AUTENTICO; con un byte cambiado → ALTERADO; tras cambiar en la BD la cantidad de un ítem firmado → ALTERADO.

- [ ] T036 [P] [US5] Prueba unitaria `B/tests/unitarias/test_verificar_pdf.py` (EQ-02, con `FirmadorEd25519` real de `cryptography`): auténtico; un byte cambiado → la firma Ed25519 ya no es válida → ALTERADO; sin código → ALTERADO "no es un documento emitido por el SGA"; código desconocido → ALTERADO; firmas incluidas alteradas → ALTERADO (research §5)
- [ ] T037 [US5] Implementar `VerificarPdf` en `B/app/modules/signing/aplicacion/verificar_pdf.py` (pasos 2, 3, 5 y 6 de research §5; recibe la verificación de firmas de 001 como dependencia)
- [ ] T038 [P] [US5] Prueba de integración `B/tests/integracion/test_eq02_pdf.py`: auténtico → AUTENTICO con código, requerimiento y emisión; un byte cambiado → ALTERADO; **EQ-02**: cambiar en la BD la cantidad de un ítem firmado (como en `test_eq02_integridad.py`) y subir el PDF original → ALTERADO; no-PDF, vacío y > 5 MB → 422; PDF de otra unidad → 404; sin sesión → 401
- [ ] T039 [US5] Crear `B/app/modules/requests/aplicacion/verificar_pdf_subido.py` (validación del paso 1, visibilidad del paso 4) y la ruta `POST /api/v1/documentos/verificacion` con cuerpo `application/pdf` en un router `documentos` registrado en `B/app/main.py`, con `VerificacionPdfSalida` en `B/app/modules/requests/presentacion/esquemas.py`
- [ ] T040 [P] [US5] Prueba Jest `F/tests/paginas/VerificarDocumento.test.tsx`: elegir archivo y verificar → "Auténtico" con código y sellos; "Alterado" con el motivo; archivo no PDF → mensaje sin llamar a la API; error 404/422 mostrado
- [ ] T041 [US5] Agregar `verificarPdf(archivo)` a `F/src/api/cliente.ts` (con prueba), crear `F/src/paginas/VerificarDocumento.tsx`, la ruta protegida `/verificar` en `F/src/App.tsx` y el enlace "Verificar PDF" (ícono `ShieldCheck`) en `F/src/componentes/Encabezado.tsx`, con su prueba en `F/tests/componentes/Encabezado.test.tsx`

**Checkpoint**: las cinco historias funcionan.

---

## Phase 8: Polish & Cross-Cutting

- [ ] T042 [P] Agregar a `tecnologia/pruebas/postman/sga-001.postman_collection.json` los casos de documento, descarga del PDF, verificación (AUTENTICO) y 404 ajeno, y ejecutarla con Newman
- [ ] T043 [P] Actualizar la descripción de `GET /{id}/verificacion` en `B/app/modules/requests/presentacion/router.py` (ya no menciona DT-01) y las cabeceras de `tecnologia/nginx/default.conf` y `tecnologia/docker-compose.yml` que citan el PDF pendiente
- [ ] T044 Generar la evidencia EQ-02 con el PDF en `evidencias/EQ-02/`: un PDF auténtico, el mismo con un byte cambiado, y el JSON de ambas verificaciones (AUTENTICO y ALTERADO); agregarla a `evidencias/README.md`
- [ ] T045 Ejecutar `specs/002-documento-firmado/quickstart.md` de punta a punta contra `docker compose up --build -d`, medir con `curl -w %{time_total}` que la descarga del PDF y la verificación tarden < 3 s (SC-006) y corregir lo que falle
- [ ] T046 Revisión final: Ruff, pytest con cobertura ≥ 60 % en los módulos críticos, ESLint, `tsc`, Jest con cobertura, sin secretos en el repositorio

---

## Dependencies & Execution Order

- **Setup (F1)** → **Foundational (F2)** → historias.
- **US1** es la base de US2 (la casilla muestra el documento) y de US3 (el PDF usa `ConsultarDocumento`).
- **US4** depende de US3 (`EmitirDocumento`, `DescargarPdf`). **US5** depende de US3 (necesita PDF emitidos).
- Orden: F1 → F2 → US1 → US2 → US3 → US4 → US5 → Polish. US2 y US3 pueden avanzar en paralelo después de US1.

## Parallel Example: User Story 3

```text
T026 (unitaria EmitirDocumento)  ‖  T028 (integración descarga)  ‖  T030 (descargarPdf en el cliente)
```

## Implementation Strategy

1. MVP: F1 + F2 + US1 (el documento visible) → validar y desplegar.
2. US2 (revisión) → US3 (PDF) → US4 (acta) → US5 (verificación, EQ-02).
3. Polish: Postman, evidencia EQ-02 y quickstart. El cierre de DT-01 y la prórroga de DT-02 quedan en la enmienda v1.3.0 de la constitución, que se hace antes de implementar.
