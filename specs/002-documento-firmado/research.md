# Research: Documento firmado y PDF verificable (002)

## §1. Qué se firma en el PDF

- **Decisión**: se firman los **bytes del PDF**. Al emitirlo se calcula `SHA-256(bytes)` y se firma
  con `FirmadorEd25519` (método `ed25519-sha256-v1`, la misma clave del sistema de 001). La huella y
  la firma se guardan en `documento_emitido`.
- **Por qué**: EQ-02 dice literalmente "cambia un byte del PDF firmado y comprueba que la firma
  Ed25519 ya no es válida". Reutilizar el firmador de 001 evita otra clave y otro método.
- **Alternativas**: firma PAdES embebida en el PDF (necesita certificados X.509 y una librería
  extra; RC01 ya acepta que la firma no tiene validez legal plena); firmar solo el contenido
  canónico (no detectaría un PDF editado que conserve los datos).

## §2. Huella impresa en el PDF

- **Decisión**: el PDF imprime la **huella del contenido** (`huella_contenido`): SHA-256 del JSON
  canónico del documento (encabezado, ítems y la huella de cada sello). La huella de los bytes no
  puede imprimirse dentro del mismo archivo, porque cambiaría el archivo.
- **Por qué**: cumple "el PDF incluye la huella" y permite cotejar a simple vista que el documento
  corresponde a esos datos.

## §3. Código de verificación

- **Decisión**: `SGA-XXXX-XXXX-XXXX` con 12 caracteres aleatorios del alfabeto base32 sin
  ambigüedades (`secrets`), ~60 bits. Va impreso en el pie de cada página y en los metadatos del PDF
  (`Keywords`), que ReportLab escribe sin comprimir; se extrae con una expresión regular sobre los
  bytes, sin leer el PDF con otra librería.
- **Alternativas**: derivarlo del id o de la huella (revela datos o no existe antes de generar el
  PDF); pedir al usuario que lo escriba (peor experiencia y no hace falta).

## §4. Cuándo se emite (clarificación 1)

- **Decisión**: a pedido. `GET …/documento.pdf` busca el documento emitido para (requerimiento,
  tipo, última firma incluida). Si existe, lee el archivo del almacenamiento, comprueba su huella y
  lo entrega; si no, genera, firma, guarda el archivo y luego la fila, dentro de la Unidad de Trabajo
  de la petición. Dos descargas simultáneas: el índice único hace fallar la segunda inserción, que
  vuelve a leer y entrega el documento ya emitido.
- **Si falla la confirmación**: queda un archivo huérfano con un nombre que nadie referencia; es
  inofensivo (no se sobrescribe ni se sirve) y se documenta.
- **Por qué**: la firma de los niveles (EQ-04) no se hace más lenta y las solicitudes firmadas en
  001 obtienen su PDF sin migrar datos.

## §5. Verificación de un PDF subido

Orden: (1) validar que no está vacío, que empieza con `%PDF-` y que pesa ≤ 5 MB → si no, 422;
(2) extraer el código → si no hay, ALTERADO "no es un documento emitido por el SGA"; (3) buscar el
documento → si no existe, ALTERADO "código de verificación no reconocido"; (4) aplicar la
visibilidad del requerimiento (ajeno → 404); (5) comparar `SHA-256(bytes)` con la huella y
verificar la firma Ed25519 → si falla, ALTERADO "el archivo no coincide con el documento emitido";
(6) verificar con los datos actuales cada firma incluida (servicio de 001) → si alguna es ALTERADA,
ALTERADO "los datos firmados del requerimiento fueron alterados"; (7) AUTENTICO.

## §6. Cómo llega el archivo

- **Decisión**: `POST /api/v1/documentos/verificacion` con el cuerpo `application/pdf` (los bytes
  tal cual). La interfaz envía el `File` del `<input type="file">` como cuerpo.
- **Por qué**: `multipart/form-data` en FastAPI exige `python-multipart`, otra dependencia. Nginx
  necesita `client_max_body_size 6m`.

## §7. Almacenamiento (ADR-010)

- **Decisión**: puerto `AlmacenDocumentos` con `guardar(clave, contenido)` (falla si la clave ya
  existe: los PDF no se sobrescriben) y `leer(clave)`. Adaptador `AlmacenDocumentosDisco` sobre
  `DOCUMENTOS_DIR` (`/datos/documentos` en el contenedor, volumen `documentos`); la clave es
  `<requerimiento_id>/<tipo>-<codigo>.pdf`, se valida que no salga de la carpeta y se escribe con
  `open(..., "xb")` en un archivo temporal y `os.link`/renombrado atómico. No hay `eliminar`.
- **Dockerfile**: crea `/datos/documentos` con dueño `sga` antes de `USER sga`, para que el volumen
  nuevo herede los permisos.

## §8. Generación con ReportLab

- **Decisión**: `platypus` (`SimpleDocTemplate`, `Table`, `Paragraph`) en A4, fuente Helvetica,
  encabezado institucional sin escudos ni logos oficiales, tabla de ítems, un sello por firma
  (recuadro con nivel, decisión, cargo, órgano, fecha, hora, método y huella abreviada), y pie con
  el código y "Página N". La fecha y hora se muestran en la hora de Perú (UTC−5).
- **Alternativas**: WeasyPrint (no es la de `docs/` y necesita librerías del sistema).

## §9. Revisión antes de firmar

- **Decisión**: `DecisionFirmaEntrada.documento_revisado: bool` obligatorio; si no es `true`, 422.
  En la interfaz, la casilla vive dentro de los diálogos de firmar y rechazar, junto al documento.
  La colección Postman y las pruebas de 001 se actualizan para enviar el campo.
