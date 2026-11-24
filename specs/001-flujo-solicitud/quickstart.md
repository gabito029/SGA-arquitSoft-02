# Quickstart: Incremento 001 — Flujo principal de abastecimiento

Guía para levantar el SGA en local y validar el flujo de punta a punta. Contrato de la API:
[contracts/openapi.yaml](contracts/openapi.yaml) · Modelo: [data-model.md](data-model.md).

## Requisitos previos

- Docker Desktop con Docker Compose v2.
- Para desarrollo sin contenedores: Python 3.12, Node.js 20 LTS y PostgreSQL 16.
- Para las pruebas de API y de carga: Newman (`npx newman`) y [k6](https://k6.io) instalado.
- Git en la rama `001-flujo-solicitud`.

## 1. Configurar variables de entorno

```bash
cd tecnologia
cp .env.example .env          # nunca se versiona el .env
python backend/scripts/generar_clave_firma.py >> .env   # agrega FIRMA_CLAVE_PRIVADA y FIRMA_CLAVE_ID
```

Variables principales de `.env.example`: `DATABASE_URL`, `JWT_SECRETO`, `JWT_MINUTOS=60`,
`FIRMA_CLAVE_PRIVADA`, `FIRMA_CLAVE_ID`, `UMBRAL_MONTO_ALTO=50000`, `CONTRASENA_DEMO`.

## 2. Levantar el sistema

```bash
docker compose up --build -d
docker compose exec api alembic upgrade head      # migraciones
docker compose exec api python -m seeds.cargar    # datos de prueba ficticios (idempotente)
```

| Servicio | URL |
|---|---|
| Aplicación web (Nginx) | http://localhost:8080 |
| Swagger UI | http://localhost:8080/docs |
| Salud | http://localhost:8080/health → `{"estado":"OK","base_datos":"OK"}` |

## 3. Usuarios de prueba

Todos usan la contraseña definida en `CONTRASENA_DEMO`.

| Usuario | Rol | Órgano |
|---|---|---|
| `oficial.bim11` | Oficial de logística | Unidad BIM-11 (1DE) |
| `cmdte.bim11` | Comandante de la unidad | Unidad BIM-11 (1DE) |
| `jlog.1de` | Jefe de logística de la Gran Unidad | 1.ª División de Ejército |
| `jalm.sinte` | Jefe de almacén | Almacén de Intendencia |
| `almacenero.sinte` | Almacenero | Almacén de Intendencia |
| `oficial.bim21` · `jlog.2de` | Para probar el aislamiento | Unidad y División distintas |
| `auditor` | Auditor (solo consulta y verificación) | Inspectoría General |

## 4. Validar el flujo completo (demo)

1. **Registrar y enviar** (`oficial.bim11`): crear una solicitud con 2 ítems de intendencia y
   enviarla. Se espera el estado **En visto bueno de la unidad**.
2. **Visto bueno** (`cmdte.bim11`): firmar. Se espera **En conformidad de la División/Brigada**.
3. **Aislamiento** (`jlog.2de`): la solicitud no aparece en su bandeja, y abrirla por URL muestra
   "no encontrada".
4. **Conformidad** (`jlog.1de`): firmar. Se espera **En aprobación del almacén**.
5. **Aprobación** (`jalm.sinte`): firmar. Se espera **Aprobada**.
6. **Despacho** (`almacenero.sinte`): despachar las cantidades. Se espera **Despachada**, con el
   stock descontado en la pantalla de stock.
7. **Acta** (`oficial.bim11`): registrar lo recibido (con una diferencia) y firmar. Se espera
   **Recibida**.
8. **Línea de tiempo y verificación**: el detalle muestra los 6 pasos con usuario, órgano, fecha y
   estado anterior, y "Verificar" responde **Íntegra**.
9. **Bloqueo del COLOGE** (`oficial.bim11`): crear una solicitud de material de guerra y enviarla.
   Se espera el aviso *"Requiere autorización del COLOGE…"* y que siga en **Registrada**. Luego
   anularla con motivo: queda **Anulada**.
10. **Alteración** (demo de integridad):
    ```bash
    docker compose exec db psql -U sga -d sga -c "ALTER TABLE item_requerimiento DISABLE TRIGGER USER; UPDATE item_requerimiento SET cantidad_recibida = cantidad_recibida + 1 WHERE requerimiento_id = '<id>'; ALTER TABLE item_requerimiento ENABLE TRIGGER USER;"
    ```
    Al verificar de nuevo, el resultado es **Alterada**.

## 5. Pruebas y calidad

```bash
cd tecnologia/backend
ruff check . && ruff format --check .
pytest --cov=app --cov-report=term-missing --cov-report=html   # requiere PostgreSQL (DATABASE_URL_TEST)
pytest tests/integracion/test_eq01_control_acceso.py           # EQ-01
pytest tests/integracion/test_eq02_integridad.py               # EQ-02
pytest tests/integracion/test_eq03_concurrencia.py             # EQ-03
pytest tests/integracion/test_eq08_trazabilidad.py             # EQ-08 (adaptado a 001)

cd ../frontend
npm ci && npm run lint && npm run test:cov && npm run build   # Jest + cobertura (coverage/)

# Con el sistema levantado (paso 2):
cd ../pruebas
npx newman run postman/sga-001.postman_collection.json -e postman/local.postman_environment.json
k6 run --summary-export ../../evidencias/EQ-04/k6-resumen.json k6/eq04_rendimiento.js   # referencia; formal en 002
```

Resultado esperado: todas las pruebas en verde; cobertura de 60 % o más en `requests`, `rules`,
`signing` e `inventory` (pytest) y en `src/logica`, `src/auth` y `src/api` (Jest); 0 errores de
Ruff y ESLint; Newman sin fallos. Los reportes se copian a `evidencias/EQ-0X/` (fuera de `docs/`).

**Demo de respaldo**: si una pantalla no está lista, ese paso se ejecuta desde Swagger
(http://localhost:8080/docs → *Authorize* con el token del usuario) o con la colección de Postman.

## 6. Desarrollo sin contenedores (opcional)

```bash
cd tecnologia/backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
alembic upgrade head && python -m seeds.cargar && uvicorn app.main:app --reload
cd tecnologia/frontend && npm ci && npm run dev    # http://localhost:5173 (proxy /api → :8000)
```
