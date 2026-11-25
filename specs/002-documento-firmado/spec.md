# Feature Specification: Documento firmado y PDF verificable

**Feature Branch**: `002-documento-firmado`

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "Cada requerimiento se presenta como un documento oficial con formato
militar: encabezado (SGA, número de requerimiento, unidad solicitante, Gran Unidad, almacén,
fecha), tabla de ítems y un bloque de firmas. Antes de firmar, el firmante ve el documento completo
dentro de la página y confirma ('He revisado el documento'). Cada firma aparece en el documento
como un sello digital: nivel, decisión, cargo, órgano, fecha, hora, método y huella SHA-256
abreviada. El acta de recepción tiene su propio documento con lo despachado, lo recibido y las
observaciones. Cualquier usuario autorizado puede descargar el documento en PDF; el PDF incluye un
código de verificación y la huella. El sistema verifica un PDF subido por el usuario, indicando si
es auténtico o si fue alterado. Los PDF se guardan mediante la interfaz de almacenamiento de
documentos de ADR-010 (en disco local, en un volumen de Docker)."

## Fuente de verdad y conflictos con el pedido

Según la constitución (principio I), `docs/` prevalece sobre el pedido; los conflictos se
reportan aquí y no se resuelven en silencio. Este incremento completa **RF05** ("generar un
documento PDF y verificar si fue alterado") para HU03, HU05, HU08 y HU12, aplica **ADR-004** (PDF
verificable) y **ADR-010** (almacenamiento de documentos mediante una interfaz), valida **EQ-02**
con el PDF y **cierra la desviación temporal DT-01** de la constitución v1.2.0.

| # | Pedido original | Lo que fija `docs/` | Cómo queda en esta especificación |
|---|---|---|---|
| C1 | "El sistema verifica un PDF … si es auténtico o si fue alterado" | EQ-02: la verificación responde **ALTERADO** (cambiar un byte del PDF invalida la firma Ed25519) | El resultado de verificar un PDF es **AUTÉNTICO** o **ALTERADO** (masculino: "el documento"), literal a EQ-02. La verificación de firmas del requerimiento de 001 conserva INTEGRA/ALTERADA ("la firma") |
| C2 | "Cualquier usuario autorizado puede descargar" | Acceso por rol y órgano en cada petición; recurso de otra unidad 404 (EQ-01, principio X) | "Autorizado" = quien puede ver ese requerimiento según la visibilidad de 001; los demás reciben 404 |
| C3 | Sellos con "método" de firma | ADR-004: SHA-256 + Ed25519 con la clave del sistema; sin validez legal plena (RC01) | El sello muestra el método `ed25519-sha256-v1` y el documento indica que es una firma con la clave del sistema |
| C4 | Los PDF en disco local, en un volumen de Docker | ADR-010 y C4 nivel 2: "Almacenamiento de documentos", volumen en disco del servidor; los PDF firmados **no se modifican** | Los PDF se guardan una sola vez y nunca se sobrescriben; un documento nuevo es un archivo nuevo |
| C5 | — | C4 nivel 2: "Documentos de cada firma y actas de recepción" | Hay un documento PDF por cada estado firmado del requerimiento (uno por firma) y uno del acta |
| C6 | — | COLOGE (HU04, RN03) y aprobación automática (RN04) | Fuera de este incremento: el bloque de firmas muestra los niveles que existen hoy; un nivel nuevo aparecerá como un sello más sin cambiar el documento |

## Clarifications

### Session 2026-11-24

Preguntas respondidas por la autora del flujo con la opción más simple que respeta `docs/`:

- Q: ¿Cuándo se emite el PDF: en el momento de cada firma o a pedido, en la primera descarga
  después de una firma nueva? → A: A pedido, en la primera descarga después de una firma nueva; la
  firma de 001 no cambia y las solicitudes firmadas antes de 002 también obtienen su PDF.
- Q: ¿Qué valores devuelve la verificación de un PDF subido? → A: AUTENTICO o ALTERADO (literal a
  EQ-02, "el documento"); la verificación de las firmas del requerimiento de 001 conserva INTEGRA o
  ALTERADA ("la firma").
- Q: ¿Qué sellos lleva cada documento? → A: El documento del requerimiento lleva los sellos del
  conducto regular (visto bueno, conformidad, aprobación y sus rechazos); el sello del acta va solo
  en el documento del acta. Así, firmar el acta no cambia el PDF del requerimiento.
- Q: ¿La emisión de un PDF se registra en la línea de tiempo? → A: No; no es un cambio de estado,
  firma, rechazo ni movimiento (AC08). El propio registro del documento emitido guarda quién lo
  emitió y cuándo, y nunca se modifica.
- Q: ¿Quién puede verificar un PDF subido y qué ve si no tiene acceso al requerimiento? → A:
  Cualquier usuario autenticado; si el documento existe pero pertenece a un requerimiento que no
  puede ver, recibe "no encontrado" (404, EQ-01). Un archivo sin código reconocible es ALTERADO con
  el motivo "no es un documento emitido por el SGA".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el requerimiento como documento oficial (Priority: P1)

Cualquier usuario que puede ver un requerimiento lo ve también como un documento oficial con
formato militar: encabezado con SGA, número de requerimiento, unidad solicitante, Gran Unidad,
almacén y fecha; la tabla de ítems; y el bloque de firmas, donde cada firma registrada aparece como
un sello digital (nivel, decisión, cargo, órgano, fecha, hora, método y huella SHA-256 abreviada).

**Why this priority**: es la base del resto: el firmante revisa este documento, el PDF lo
reproduce y la verificación lo protege. Reemplaza el oficio en papel con sus sellos.

**Independent Test**: con una solicitud que tiene el visto bueno y la conformidad, el usuario abre
el documento y ve el encabezado completo, los ítems y dos sellos con todos sus datos.

**Acceptance Scenarios**:

1. **Dada** una solicitud enviada de U1, **Cuando** un usuario que puede verla abre el documento,
   **Entonces** ve el encabezado (SGA, número, unidad, Gran Unidad, almacén y fecha), la tabla de
   ítems (código, descripción, unidad de medida y cantidad) y el bloque de firmas.
2. **Dada** una solicitud con firmas registradas, **Cuando** se abre el documento, **Entonces**
   cada firma aparece como un sello con nivel, decisión (aprobó o rechazó), cargo, órgano, fecha,
   hora, método y huella abreviada, en el orden del conducto regular.
3. **Dada** una solicitud sin firmas, **Cuando** se abre el documento, **Entonces** el bloque de
   firmas indica que todavía no hay firmas.
4. **Dada** una solicitud de otra unidad, **Cuando** un usuario sin acceso intenta abrir su
   documento, **Entonces** el sistema responde como si no existiera.

---

### User Story 2 - Revisar el documento antes de firmar (Priority: P1)

Antes de firmar (aprobar o rechazar) un nivel, el firmante ve el documento completo dentro de la
misma página y marca "He revisado el documento". Sin esa confirmación no puede firmar.

**Why this priority**: la firma digital solo tiene sentido si el firmante vio lo que firma; es la
costumbre del oficio en papel ("leído y conforme").

**Independent Test**: el comandante abre una solicitud pendiente de su visto bueno; el botón de
firmar está deshabilitado hasta que marca la confirmación; si el sistema recibe una firma sin
confirmación, la rechaza.

**Acceptance Scenarios**:

1. **Dada** una solicitud pendiente del nivel del usuario, **Cuando** abre la acción de firmar o
   rechazar, **Entonces** ve el documento completo en la página y la casilla "He revisado el
   documento", sin marcar.
2. **Dada** la casilla sin marcar, **Cuando** el firmante intenta firmar o rechazar, **Entonces** la
   acción no se envía y la interfaz indica que debe revisar el documento.
3. **Dada** una petición de firma o rechazo que no declara la revisión, **Cuando** llega al sistema,
   **Entonces** se rechaza como dato inválido y no se registra ninguna firma.
4. **Dada** la casilla marcada, **Cuando** el firmante confirma, **Entonces** la firma se registra
   como en el incremento 001 y aparece como un sello nuevo en el documento.

---

### User Story 3 - Descargar el documento en PDF con código de verificación (Priority: P1)

Cualquier usuario autorizado descarga el documento del requerimiento en PDF. El PDF reproduce el
documento oficial con sus sellos e incluye un código de verificación y la huella SHA-256. El PDF
queda firmado por el sistema y guardado sin cambios.

**Why this priority**: es lo que pide RF05 y lo que falta para cerrar DT-01; el PDF es el documento
que circula fuera del sistema.

**Independent Test**: con una solicitud firmada, el usuario descarga el PDF; el archivo se abre en
cualquier lector, muestra el encabezado, los ítems, los sellos, el código y la huella; dos
descargas sin firmas nuevas entre ellas devuelven el mismo archivo.

**Acceptance Scenarios**:

1. **Dada** una solicitud con al menos una firma, **Cuando** un usuario autorizado descarga el PDF,
   **Entonces** recibe un PDF con el encabezado, los ítems, un sello por firma, el código de
   verificación y la huella del documento.
2. **Dada** una solicitud ya descargada, **Cuando** se descarga otra vez sin firmas nuevas,
   **Entonces** el sistema devuelve el mismo PDF guardado (mismo código, mismos bytes).
3. **Dada** una solicitud con una firma nueva desde la última descarga, **Cuando** se descarga,
   **Entonces** se emite un PDF nuevo con un código nuevo (la firma del acta no cuenta: solo cambia
   el PDF del acta), y el PDF anterior se conserva sin
   cambios y sigue siendo verificable.
4. **Dada** una solicitud sin firmas, **Cuando** se intenta descargar el PDF, **Entonces** el
   sistema indica que todavía no hay un documento firmado que descargar.
5. **Dada** una solicitud de otra unidad, **Cuando** un usuario sin acceso intenta descargar su PDF,
   **Entonces** el sistema responde como si no existiera.

---

### User Story 4 - Documento y PDF del acta de recepción (Priority: P1)

El acta de recepción firmada tiene su propio documento: encabezado del requerimiento, por cada
ítem lo despachado, lo recibido y la observación, la indicación de si hubo diferencias y el sello
del oficial de logística que la firmó. Se ve en la página y se descarga en PDF con su propio
código de verificación y huella.

**Why this priority**: el acta cierra el flujo y es el documento que más se audita (HU08, HU12).

**Independent Test**: con una solicitud "Recibida" con una diferencia, el usuario abre el acta y
descarga su PDF; ambos muestran la fila con la diferencia y el sello del acta.

**Acceptance Scenarios**:

1. **Dada** una solicitud con el acta firmada, **Cuando** un usuario autorizado abre el documento
   del acta, **Entonces** ve lo despachado, lo recibido y la observación de cada ítem, si hubo
   diferencias y el sello del acta.
2. **Dada** el acta firmada, **Cuando** se descarga su PDF, **Entonces** contiene esos datos, un
   código de verificación propio y la huella, distintos de los del PDF del requerimiento.
3. **Dada** una solicitud sin acta firmada, **Cuando** se pide el documento o el PDF del acta,
   **Entonces** el sistema indica que el acta no existe todavía.

---

### User Story 5 - Verificar un PDF subido (Priority: P1)

Un usuario autenticado (por ejemplo, el auditor) sube un PDF y el sistema le indica si es
**auténtico** (emitido por el SGA, sin cambios, y con las firmas que contiene todavía íntegras) o
**alterado**, con el código del documento, el requerimiento al que pertenece y la fecha de
emisión cuando el usuario tiene acceso a ese requerimiento.

**Why this priority**: es la respuesta esperada de EQ-02 y la función del auditor (HU12); sin ella
el código y la huella del PDF no sirven de nada.

**Independent Test**: se descarga un PDF y se sube tal cual: "Auténtico". Se cambia un solo byte y
se sube: "Alterado". Se cambia en la base de datos la cantidad de un ítem firmado y se sube el PDF
original: "Alterado".

**Acceptance Scenarios**:

1. **Dado** un PDF descargado del SGA sin cambios, **Cuando** se sube para verificarlo,
   **Entonces** el resultado es "Auténtico", con el código, el requerimiento y la fecha de emisión.
2. **Dado** un PDF del SGA con cualquier byte cambiado, **Cuando** se sube, **Entonces** el
   resultado es "Alterado".
3. **Dado** un PDF del SGA auténtico cuyo requerimiento tiene un dato firmado alterado en la base
   de datos, **Cuando** se sube, **Entonces** el resultado es "Alterado", indicando que los datos
   firmados ya no coinciden.
4. **Dado** un archivo que no es un PDF, o que supera el tamaño máximo, **Cuando** se sube,
   **Entonces** se rechaza como dato inválido sin verificarlo.
5. **Dado** un PDF que el SGA no emitió (sin código de verificación reconocible), **Cuando** se
   sube, **Entonces** el resultado es "Alterado", con el motivo "no es un documento emitido por el
   SGA".
6. **Dado** un PDF auténtico de un requerimiento que el usuario no puede ver, **Cuando** lo sube,
   **Entonces** el sistema responde como si el documento no existiera (no revela su contenido).

---

### Edge Cases

- **Dos descargas simultáneas** del mismo documento sin PDF emitido: se emite un solo PDF y ambas
  reciben el mismo archivo.
- **El archivo guardado se pierde o se modifica en el disco**: la descarga no devuelve un archivo
  distinto del emitido; informa que el documento guardado no coincide con su huella.
- **El PDF se emitió antes de un rechazo o de firmas posteriores**: sigue siendo auténtico, porque
  refleja fielmente el estado firmado en el que se emitió.
- **Solicitudes firmadas en el incremento 001** (sin PDF): su primer PDF se emite en la primera
  descarga, con los mismos sellos.
- **Rechazos**: el sello muestra la decisión "Rechazó"; el motivo aparece en el documento.
- **Nombres largos o muchos ítems**: el documento y el PDF continúan en varias páginas, con el
  código de verificación en cada página.
- **Datos personales**: el PDF no incluye contraseñas, la clave de firma ni identificadores
  internos innecesarios.
- **Archivo vacío o PDF dañado** al verificar: se rechaza como dato inválido.

## Requirements *(mandatory)*

### Functional Requirements

**Documento del requerimiento**

- **FR-001**: El sistema DEBE presentar cada requerimiento como un documento oficial con un
  encabezado que contenga: SGA (Sistema de Gestión de Almacén con Firma Digital), número de
  requerimiento, unidad solicitante, Gran Unidad, almacén y fecha de registro.
- **FR-002**: El documento DEBE incluir la tabla de ítems: código, descripción, unidad de medida,
  categoría y cantidad solicitada.
- **FR-003**: El documento DEBE incluir un bloque de firmas con un sello digital por cada firma
  del conducto regular registrada (visto bueno, conformidad, aprobación o sus rechazos; el sello
  del acta va solo en el documento del acta, FR-014), en el orden del conducto regular, con: nivel, decisión, cargo (rol), órgano, fecha,
  hora, método de firma y huella SHA-256 abreviada (primeros y últimos 8 caracteres), y el motivo
  si la decisión es rechazar.
- **FR-004**: El documento DEBE ser visible para los mismos usuarios que pueden ver el
  requerimiento (visibilidad de 001); para los demás, el sistema DEBE responder como si no
  existiera.

**Revisión antes de firmar**

- **FR-005**: Antes de firmar o rechazar un nivel, la interfaz DEBE mostrar el documento completo
  en la misma página y una casilla "He revisado el documento", desmarcada por defecto.
  El acta de recepción no usa esta casilla: su formulario ya muestra todo lo que se firma (lo
  despachado, lo recibido y las observaciones de cada ítem).
- **FR-006**: La interfaz NO DEBE enviar la firma o el rechazo mientras la casilla esté desmarcada.
- **FR-007**: El sistema DEBE rechazar como dato inválido toda petición de firma o rechazo que no
  declare que el documento fue revisado, sin registrar nada.

**PDF del requerimiento y del acta**

- **FR-008**: Un usuario que puede ver el requerimiento DEBE poder descargar su documento en PDF
  cuando el requerimiento tiene al menos una firma; si no tiene firmas, el sistema DEBE indicarlo.
- **FR-009**: El PDF DEBE reproducir el documento (encabezado, ítems y sellos) e incluir en cada
  página un **código de verificación** único y, al final, la **huella SHA-256** del contenido
  firmado del documento y la leyenda de que la firma usa la clave del sistema.
- **FR-010**: Al emitir un PDF, el sistema DEBE calcular la huella SHA-256 de sus bytes, firmarla
  con Ed25519 usando la clave del sistema (ADR-004) y registrar el código, la huella, la firma, el
  requerimiento, el tipo de documento, la última firma que incluye, quién lo emitió y cuándo.
- **FR-011**: Cada PDF emitido DEBE guardarse a través de la interfaz de almacenamiento de
  documentos (ADR-010) y NUNCA sobrescribirse ni eliminarse.
- **FR-012**: El PDF se emite a pedido, en la primera descarga después de una firma nueva del
  documento. Mientras no haya firmas nuevas, las descargas DEBEN devolver el PDF ya emitido; con
  una firma nueva, la siguiente descarga DEBE emitir un PDF nuevo con un código nuevo, conservando
  los anteriores.
- **FR-013**: Antes de entregar un PDF guardado, el sistema DEBE comprobar que sus bytes coinciden
  con la huella registrada; si no coinciden, NO DEBE entregarlo y DEBE informar el problema.
- **FR-014**: El acta de recepción firmada DEBE tener su propio documento y PDF, con el encabezado
  del requerimiento, por cada ítem lo despachado, lo recibido y la observación, si hubo
  diferencias y el sello del acta, con su propio código de verificación y huella.
- **FR-015**: Las solicitudes firmadas antes de este incremento DEBEN poder descargar su PDF; se
  emite en la primera descarga.

**Verificación de un PDF subido**

- **FR-016**: Un usuario autenticado DEBE poder subir un PDF para verificarlo. El sistema DEBE
  rechazar como dato inválido lo que no sea un PDF o supere 5 MB.
- **FR-017**: El resultado DEBE ser **AUTÉNTICO** solo si se cumplen todas estas condiciones: el
  código de verificación del archivo corresponde a un documento emitido; la huella SHA-256 de los
  bytes subidos es igual a la registrada; la firma Ed25519 registrada es válida para esa huella; y
  las firmas del requerimiento incluidas en ese documento siguen íntegras con los datos actuales.
  En cualquier otro caso el resultado DEBE ser **ALTERADO**, con el motivo. La API usa los
  valores `AUTENTICO` y `ALTERADO` (sin tilde); la interfaz muestra "Auténtico" y "Alterado".
- **FR-018**: Si el documento pertenece a un requerimiento que el usuario no puede ver, el sistema
  DEBE responder como si no existiera.
- **FR-019**: Con el resultado AUTÉNTICO, el sistema DEBE mostrar el código, el tipo de documento,
  el número del requerimiento, la fecha y hora de emisión y los sellos que contiene.

**Trazabilidad, seguridad y almacenamiento**

- **FR-020**: Cada emisión de PDF DEBE quedar registrada en el propio documento emitido (quién lo
  emitió, su órgano y la fecha y hora), sin cambiar el estado del requerimiento ni agregar entradas
  a la línea de tiempo, que sigue registrando solo cambios de estado, firmas, rechazos y
  movimientos (AC08).
- **FR-021**: El almacenamiento de documentos DEBE estar detrás de una interfaz: cambiar el disco
  local por otro almacenamiento NO DEBE modificar las reglas del negocio ni los casos de uso
  (ADR-010). La implementación de este incremento guarda los PDF en el disco local, en un volumen
  persistente del entorno de contenedores.
- **FR-022**: Todas las nuevas funciones DEBEN requerir sesión (sin sesión, 401) y respetar el
  control por rol y órgano (EQ-01).
- **FR-023**: La interfaz DEBE ofrecer en el detalle del requerimiento: ver el documento, descargar
  el PDF, ver y descargar el acta, y una pantalla para subir y verificar un PDF, sin diálogos
  nativos del navegador.

### Key Entities *(include if feature involves data)*

- **Documento emitido**: un PDF emitido por el SGA. Atributos: código de verificación (único),
  tipo (REQUERIMIENTO o ACTA), requerimiento, última firma incluida, huella SHA-256 de los bytes,
  firma Ed25519 de esa huella, método, clave, ubicación en el almacenamiento, tamaño, quién lo
  emitió y cuándo. No se modifica ni se elimina.
- **Sello digital**: la presentación de una firma registrada (001) en el documento: nivel,
  decisión, cargo, órgano, fecha, hora, método y huella abreviada. No es un dato nuevo.
- **Resultado de verificación de PDF**: AUTÉNTICO o ALTERADO, con el motivo y, si corresponde, los
  datos del documento emitido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (Integridad, EQ-02): el 100 % de los PDF con al menos un byte cambiado se verifica
  como ALTERADO, y el 100 % de los PDF auténticos sin cambios se verifica como AUTÉNTICO.
- **SC-002** (Integridad, EQ-02): el 100 % de las alteraciones de un dato firmado en la base de
  datos (por ejemplo, la cantidad de un ítem) hace que el PDF auténtico de ese requerimiento se
  verifique como ALTERADO.
- **SC-003** (Seguridad, EQ-01): el 100 % de los intentos de ver, descargar o verificar
  documentos de un requerimiento sin acceso responde como inexistente, y el 100 % sin sesión es
  rechazado.
- **SC-004** (Revisión): el 0 % de las firmas se registra sin la confirmación "He revisado el
  documento".
- **SC-005** (Inmutabilidad): ningún PDF emitido cambia después de emitido: dos descargas sin
  firmas nuevas devuelven archivos idénticos.
- **SC-006** (Rendimiento): un usuario descarga el PDF de un requerimiento de hasta 20 ítems en
  menos de 3 segundos, y conoce el resultado de verificar un PDF en menos de 3 segundos.
- **SC-007** (Cierre de DT-01): la firma de cada nivel y del acta tiene un PDF verificable, y la
  constitución ya no registra DT-01 como abierta.

## Assumptions

- La firma con la clave del sistema no tiene validez legal plena (RC01); el documento lo indica.
- El código de verificación es un identificador aleatorio, legible y único (no revela datos), que
  el PDF lleva impreso y en sus metadatos; no hace falta escribirlo a mano para verificar.
- El firmante revisa el documento en la página (vista HTML con los mismos datos que el PDF); el
  PDF se emite a pedido, después de la firma.
- El PDF no se firma con un certificado embebido en el formato PDF (PAdES): la firma Ed25519 de
  sus bytes se registra en el sistema y se comprueba al verificar.
- El tamaño máximo de un PDF subido es 5 MB, suficiente para documentos de hasta cientos de ítems.
- Fuera de alcance: HTTPS (desviación temporal DT-02, sigue abierta), la autorización del COLOGE,
  la aprobación automática, la verificación de la auditoría encadenada por el auditor, el envío del
  PDF por correo, la firma con certificados acreditados y la conversión a otros formatos.
