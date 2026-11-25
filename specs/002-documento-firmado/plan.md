# Implementation Plan: Documento firmado y PDF verificable (incremento 002)

**Branch**: `002-documento-firmado` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-documento-firmado/spec.md`

## Summary

Cada requerimiento se presenta como un documento oficial (encabezado, ítems y sellos digitales) que
el firmante revisa en la página antes de firmar. El documento, y aparte el acta de recepción, se
descargan en PDF generado con **ReportLab**, con un código de verificación y la huella del
contenido. Cada PDF se emite una sola vez por estado firmado: el sistema calcula la huella SHA-256
de sus bytes, la firma con **Ed25519** (la misma clave del sistema de 001, ADR-004) y guarda el
archivo a través del puerto **`AlmacenDocumentos`** (ADR-010), cuyo adaptador de disco escribe en
un volumen de Docker. Un PDF subido se verifica: AUTENTICO si su código existe, sus bytes coinciden
con la huella firmada y las firmas que contiene siguen íntegras con los datos actuales; si no,
ALTERADO (EQ-02). Con esto se **cierra la desviación temporal DT-01**. Decisiones en
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend) · TypeScript 5 / React 18 (frontend)

**Primary Dependencies**: las de 001 más **ReportLab ≥ 4.2** (ADR-011, diseño interno de `docs/`).
Sin `python-multipart`: el PDF a verificar llega como cuerpo `application/pdf` (research §6).

**Storage**: PostgreSQL 16 (tabla nueva `documento_emitido`, inmutable) y disco local para los PDF
(`/datos/documentos`, volumen `documentos` de Docker Compose) detrás de `AlmacenDocumentos`.

**Testing**: pytest (unitarias con dobles de los puertos), pytest + httpx contra PostgreSQL,
pytest-cov, Ruff · Jest + Testing Library, ESLint, `tsc` · Postman/Newman (casos nuevos).

**Target Platform**: contenedores Linux con Docker Compose; navegador de escritorio y celular

**Project Type**: aplicación web (API REST + SPA)

**Performance Goals**: emitir y descargar el PDF de hasta 20 ítems en < 3 s; verificar un PDF en
< 3 s (SC-006). La firma de los niveles no se hace más lenta: el PDF se emite a pedido.

**Constraints**: PDF inmutables (nunca se sobrescriben ni se borran); máximo 5 MB al verificar;
API sin estado; secretos fuera del repositorio; `docs/` no se modifica; sin `window.confirm` ni
`alert`.

**Scale/Scope**: 5 endpoints nuevos (documento JSON del requerimiento y del acta, PDF del
requerimiento, PDF del acta y verificación de PDF) y un cambio compatible en la firma (`documento_revisado`); 1 tabla; 1
pantalla nueva (Verificar PDF) y 2 componentes (documento oficial, casilla de revisión).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Fidelidad a `docs/` | ReportLab, Ed25519 y `AlmacenDocumentos` con adaptador de disco, tal como fijan ADR-004, ADR-010, ADR-011 y el C4; `docs/` no se modifica | ✅ con un conflicto reportado (abajo, DV-10) |
| II. Especificaciones SDD | `spec.md` con 5 historias trazadas a RF05, HU03, HU05, HU08 y HU12, y clarificaciones registradas | ✅ |
| III. Desarrollo incremental | Fases por historia; cada una deja el sistema funcionando y en verde | ✅ |
| IV. API REST documentada | Endpoints bajo `/api/v1`, en `contracts/openapi.yaml` y en `/docs`, con 401, 404, 409 y 422 | ✅ |
| V. Diseño limpio | Puertos `AlmacenDocumentos` y `GeneradorPdf` en el dominio de `signing`; adaptadores en infraestructura; los casos de uso no importan ReportLab ni el disco | ✅ |
| VI. Pruebas (NO NEGOCIABLE) | pytest unitarias e integración, Jest para la casilla, el documento y la verificación; cobertura ≥ 60 %; CI en verde | ✅ |
| VII. Atributos de calidad | EQ-02 con el PDF (un byte cambiado → ALTERADO; dato de la base cambiado → ALTERADO) y su evidencia en `evidencias/EQ-02/` | ✅ |
| VIII. Datos y caché | Migración Alembic `0003`, índice único por (requerimiento, tipo, última firma), disparador de inmutabilidad; sin caché nueva | ✅ |
| IX. Reglas de dominio | Firma Ed25519 con `cryptography`; PDF verificable de cada nivel y del acta: **cierra DT-01**; nada se elimina | ✅ |
| X. Actores y seguridad | JWT y visibilidad de 001 en cada endpoint (ajeno → 404); límite de tamaño; la clave sigue en el entorno | ✅ con DT-02 (HTTPS) prorrogada expresamente por la enmienda v1.3.0 de la constitución (decisión de la autora del 2026-11-24): 002 cierra solo DT-01 |
| XI. Español y Conventional Commits | Código, documentación y commits en español | ✅ |

**Conflictos reportados (principio I)**:

1. **Ubicación del adaptador (DV-10)**: el diseño interno de `docs/` lista
   `almacen_documentos_disco.py` bajo `requests/infraestructura/` con la nota "implementa
   AlmacenDocumentos y genera el PDF con ReportLab", mientras que el C4 nivel 3 asigna "generación
   del PDF y verificación" al módulo **Firma digital** (`modules/signing/`). Se sigue el C4: el
   puerto y su adaptador `almacen_documentos_disco.py` (mismo nombre de archivo) viven en
   `signing`, y la generación con ReportLab va en un adaptador propio (`generador_pdf_reportlab.py`)
   para respetar la responsabilidad única que pide `principios-de-diseno.md`. `requests` sigue
   siendo quien aplica la visibilidad y arma los datos, y llama a `signing` por su servicio público,
   como en 001.
2. **Término del resultado**: EQ-02 dice ALTERADO; 001 usa ALTERADA para las firmas. La
   verificación de un PDF usa AUTENTICO/ALTERADO, literal a EQ-02; la de firmas de 001 no cambia
   (clarificación del 2026-11-24). La constitución se enmienda para registrarlo.

3. **Cierre de las desviaciones temporales**: la constitución v1.2.0 exige cerrar DT-01 y DT-02 en
   002 y no admite prorrogarlas sin enmienda. Por decisión de la autora (2026-11-24), este
   incremento cierra solo DT-01; la constitución se enmienda a v1.3.0 **antes de implementar**
   para cerrar DT-01 y prorrogar DT-02 (HTTPS) con un plazo explícito.

**Resultado del gate**: aprobado, condicionado a la enmienda v1.3.0.
**Re-evaluación tras la Fase 1**: aprobado; el diseño no agrega contenedores (el volumen ya figura
en el C4 nivel 2 como "Almacenamiento de documentos").

## Arquitectura aplicada

| Módulo | Qué cambia en 002 |
|---|---|
| `signing` | Puertos `AlmacenDocumentos`, `GeneradorPdf` y `RepositorioDocumentos`; modelo `DocumentoPdf` (Python puro); casos de uso `EmitirDocumento` y `VerificarPdf`; adaptadores `almacen_documentos_disco.py`, `generador_pdf_reportlab.py` y `repositorio_documentos_postgres.py` |
| `requests` | Casos de uso `ConsultarDocumento`, `DescargarPdf` y `VerificarPdfSubido`, que aplican la visibilidad de 001 (`cargar_visible`) y arman `DocumentoPdf`; `FirmaEntrada` exige `documento_revisado`; rutas nuevas |
| `core` | `documentos_dir` y `pdf_tamano_maximo` en la configuración |
| Frontend | `DocumentoOficial`, casilla "He revisado el documento" en los diálogos de firma y rechazo, botones de descarga y página `VerificarDocumento` |

**SOLID y patrones**: Adapter (disco, ReportLab), Repository (`documento_emitido`), inyección de
dependencias en `dependencias.py`, Unit of Work de 001 (la fila del documento se guarda en la
transacción de la petición). Abierto/cerrado (ADR-010): un almacenamiento en la nube sería otro
adaptador de `AlmacenDocumentos`, sin tocar los casos de uso.

## Project Structure

### Documentation (this feature)

```text
specs/002-documento-firmado/
├── spec.md
├── plan.md              # este archivo
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml     # solo lo nuevo y lo que cambia respecto de 001
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
tecnologia/
├── docker-compose.yml               # + volumen "documentos" montado en /datos/documentos (api)
├── .env.example                     # + DOCUMENTOS_DIR, PDF_TAMANO_MAXIMO
├── nginx/default.conf               # + client_max_body_size 6m en /api/
├── backend/
│   ├── Dockerfile                   # crea /datos/documentos con dueño sga
│   ├── pyproject.toml               # + reportlab
│   ├── migrations/versions/0003_documento_emitido.py
│   ├── app/modules/signing/
│   │   ├── dominio/  documento.py (DocumentoPdf, SelloDocumento, TipoDocumento, codigo), puertos.py (+3 puertos), tipos.py (+ResultadoPdf)
│   │   ├── aplicacion/ emitir_documento.py, verificar_pdf.py
│   │   └── infraestructura/ almacen_documentos_disco.py, generador_pdf_reportlab.py,
│   │                        repositorio_documentos_postgres.py, modelos.py (+DocumentoEmitidoModelo), dependencias.py
│   ├── app/modules/requests/
│   │   ├── aplicacion/ consultar_documento.py (vista y armado de DocumentoPdf), descargar_pdf.py, verificar_pdf_subido.py
│   │   └── presentacion/ router.py (+rutas), esquemas.py (+DocumentoSalida, VerificacionPdfSalida; FirmaEntrada.documento_revisado)
│   └── tests/ unit/signing/…, integracion/test_documentos.py, test_eq02_pdf.py
├── frontend/src/
│   ├── api/cliente.ts, tipos.ts      # obtenerDocumento, descargarPdf, verificarPdf
│   ├── componentes/DocumentoOficial.tsx, CasillaRevision.tsx
│   ├── paginas/DetalleSolicitud.tsx  # documento, descargas, casilla
│   └── paginas/VerificarDocumento.tsx (+ ruta /verificar y enlace en el menú)
└── pruebas/postman/                  # + casos de documento y verificación
```

## Estrategia de pruebas

| Nivel | Qué se prueba |
|---|---|
| Unitarias (pytest, sin BD) | Código de verificación (formato, extracción de bytes); `EmitirDocumento` con dobles (reutiliza el emitido, emite uno nuevo con una firma nueva, no sobrescribe, rechaza bytes que no coinciden con la huella); `VerificarPdf` (auténtico, un byte cambiado → firma Ed25519 inválida, sin código, código desconocido, firmas alteradas); adaptador de disco (escribe, lee, se niega a sobrescribir, evita rutas fuera de la carpeta); generador ReportLab (PDF válido con código, huella y sellos) |
| Integración (pytest + httpx + PostgreSQL) | Documento JSON y visibilidad (404 ajeno, 401); firma sin `documento_revisado` → 422; descarga dos veces → mismos bytes; firma nueva → código nuevo; acta; verificación de un PDF auténtico, de uno con un byte cambiado y, **EQ-02**, de uno auténtico después de cambiar en la BD la cantidad de un ítem firmado → ALTERADO; no-PDF y > 5 MB → 422 |
| Jest | `DocumentoOficial` (encabezado, ítems, sellos, sin firmas); casilla que habilita el botón de firmar y rechazar; `VerificarDocumento` (auténtico, alterado, error); cliente (`descargarPdf`, `verificarPdf`) |
| Newman | Descargar PDF, verificar, 404 ajeno |

## CI y entorno

Sin cambios en el pipeline: Ruff, pytest con cobertura, ESLint, `tsc` y Jest ya corren en cada
push. `docker compose up --build -d` monta el volumen `documentos`; los PDF sobreviven a reinicios
y a `--scale api=2` (las dos instancias comparten el volumen).

## Complexity Tracking

| Desviación | Por qué se necesita | Alternativa más simple descartada porque |
|---|---|---|
| DV-10: `almacen_documentos_disco.py` en `signing` y no en `requests` | El C4 nivel 3 asigna el PDF a Firma digital; los dos documentos de `docs/` no coinciden | Ponerlo en `requests` haría que dos módulos generen y verifiquen documentos firmados |
| GET que emite el PDF la primera vez | La emisión es idempotente para el cliente (mismo PDF mientras no haya firmas nuevas) y así sirve para solicitudes firmadas en 001 | Un POST de emisión obliga a la interfaz a dos llamadas y no aporta nada al usuario |
