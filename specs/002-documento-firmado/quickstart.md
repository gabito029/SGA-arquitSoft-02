# Quickstart: validar el documento firmado y el PDF verificable (002)

## Requisitos

- `tecnologia/.env` creado desde `.env.example`, con `FIRMA_CLAVE_PRIVADA` (ver quickstart de 001).
- Docker Desktop en marcha.

## Levantar

```bash
cd tecnologia
docker compose up --build -d          # db, api (con el volumen "documentos") y web
curl -s http://localhost:8080/health
```

## Validar de punta a punta (curl)

1. Iniciar sesión como un usuario con una solicitud firmada (por ejemplo, el oficial de logística
   del seed) y guardar el token en `$T`.
2. `GET /api/v1/requerimientos/{id}/documento` → 200 con encabezado, ítems y sellos.
3. `POST /api/v1/requerimientos/{id}/firmas` sin `documento_revisado` → **422**.
4. `GET /api/v1/requerimientos/{id}/documento.pdf -o req.pdf` dos veces → los dos archivos son
   idénticos (`sha256sum`) y la cabecera `X-Codigo-Verificacion` es la misma.
5. `POST /api/v1/documentos/verificacion` con `--data-binary @req.pdf -H 'Content-Type:
   application/pdf'` → `AUTENTICO`.
6. Cambiar un byte (`python -c` que invierte un byte en la mitad del archivo) y verificar →
   `ALTERADO`.
7. Con una solicitud "Recibida": `GET …/acta/documento.pdf` → PDF del acta con otro código.
8. Sin token → 401; con un usuario de otra unidad → 404.

## Validar con pruebas

```bash
cd tecnologia/backend && ruff check . && pytest --cov
cd ../frontend && npm run lint && npx tsc --noEmit && npx jest --coverage
```

## En la interfaz

- Detalle de una solicitud → sección "Documento" con los sellos y el botón "Descargar PDF".
- Firmar o rechazar: el diálogo muestra el documento; el botón se habilita al marcar "He revisado
  el documento".
- Menú "Verificar PDF": subir el archivo y ver "Auténtico" o "Alterado" con el motivo.
