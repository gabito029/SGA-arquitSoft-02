# Data Model: Documento firmado y PDF verificable (002)

## Tabla nueva `documento_emitido` (migración `0003`)

| Columna | Tipo | Regla |
|---|---|---|
| `id` | uuid PK | |
| `codigo_verificacion` | varchar(20) | único; `SGA-XXXX-XXXX-XXXX` (research §3) |
| `tipo` | varchar(20) | `REQUERIMIENTO` o `ACTA` (CHECK) |
| `requerimiento_id` | uuid FK → `requerimiento.id` | |
| `ultima_firma_id` | uuid FK → `firma.id` | la firma más reciente incluida |
| `firmas_incluidas` | jsonb | lista de ids de firma incluidos, en orden |
| `huella_contenido` | char(64) | SHA-256 del contenido canónico del documento (impresa en el PDF) |
| `huella_sha256` | char(64) | SHA-256 de los bytes del PDF |
| `firma` | text | Ed25519 (base64) de esa huella |
| `metodo` | varchar(40) | `ed25519-sha256-v1` |
| `clave_id` | varchar(64) | |
| `clave_almacen` | varchar(200) | `<requerimiento_id>/<tipo>-<codigo>.pdf` |
| `tamano_bytes` | integer | > 0 |
| `emitido_por` | uuid FK → `usuario.id` | |
| `organo_id` | uuid FK → `organo.id` | órgano de quien emitió |
| `emitido_en` | timestamptz | |

- **Índices**: único (`requerimiento_id`, `tipo`, `ultima_firma_id`) — una emisión por estado
  firmado; único (`codigo_verificacion`).
- **Inmutabilidad**: disparador que rechaza `UPDATE` y `DELETE`, como `firma` en `0002`.
- La tabla pertenece al módulo `signing`; `requests` la usa solo a través del servicio público.

## Objetos del dominio de `signing` (Python puro)

- `TipoDocumento`: `REQUERIMIENTO`, `ACTA`.
- `ResultadoPdf`: `AUTENTICO`, `ALTERADO`.
- `SelloDocumento`: nivel, decisión, firmante, cargo (rol), órgano (código y nombre), firmado_en,
  método, huella SHA-256 y motivo (solo rechazos).
- `LineaDocumento`: código, descripción, unidad de medida, categoría, cantidad solicitada y, en el
  acta, despachada, recibida y observación.
- `DocumentoPdf`: tipo, número de requerimiento, unidad, Gran Unidad, almacén, fecha de registro,
  líneas, sellos y, en el acta, `tiene_diferencias`. `contenido_canonico()` y `huella_contenido()`.
- `DocumentoEmitido`: la fila de la tabla.

## Puertos nuevos (`signing/dominio/puertos.py`)

- `AlmacenDocumentos`: `guardar(clave, contenido: bytes) -> None` (lanza `DocumentoExistente` si la
  clave existe), `leer(clave) -> bytes` (lanza `DocumentoNoEncontrado`).
- `GeneradorPdf`: `generar(documento: DocumentoPdf, codigo: str, huella_contenido: str) -> bytes`.
- `RepositorioDocumentos`: `buscar(requerimiento_id, tipo, ultima_firma_id)`,
  `por_codigo(codigo)`, `guardar(documento)` (lanza `DocumentoExistente` ante el índice único).

## Qué incluye cada documento (clarificación 3)

| Tipo | Sellos | Última firma incluida |
|---|---|---|
| `REQUERIMIENTO` | Firmas de `VB_UNIDAD`, `CONFORMIDAD_GU` y `APROBACION_ALMACEN` (aprobaciones y rechazos) | La más reciente de esos niveles |
| `ACTA` | La firma `ACTA_RECEPCION` | Esa firma |

El motivo de un rechazo se toma de la línea de tiempo (entrada `RECHAZAR`), porque la firma de 001
no lo guarda.
