# SGA: Sistema de Gestión de Almacén con Firma Digital

[![CI](https://github.com/gabito029/SGA-arquitSoft-02/actions/workflows/ci.yml/badge.svg)](https://github.com/gabito029/SGA-arquitSoft-02/actions/workflows/ci.yml)

**Autora:** Rodrigo Cutipa, Gabriela Ana ·
**Curso:** IS488 Arquitectura de Software, Universidad Nacional de San Cristóbal de Huamanga
(UNSCH) · **Docente:** Ing. Lizbeth Jaico Quispe

## Descripción

Aplicación web académica para gestionar los requerimientos de materiales que las unidades del
**Ejército del Perú** hacen a sus almacenes. Reemplaza los oficios en papel y las firmas físicas
por requerimientos digitales que recorren el **conducto regular** (unidad, División o Brigada y
almacén), con una **firma digital Ed25519** en cada nivel, despacho con control de stock, **acta de
recepción firmada**, línea de tiempo auditada y **PDF verificable** de cada documento firmado.

- **Problema:** cada requerimiento exige oficios con firmas físicas en cada nivel, no hay
  visibilidad del estado de un pedido y no existe un sistema único para controlar el inventario.
- **Caso de estudio:** Comando Logístico del Ejército (COLOGE), Servicio de Intendencia y unidades
  de las Divisiones de Ejército. Todos los datos del sistema son ficticios.

## Arquitectura

La arquitectura se diseñó en el Sprint 1 y está en [`docs/`](docs/), que es la fuente de verdad del
proyecto.

| Tema | Decisión | Documento |
|---|---|---|
| Estilo | Monolito modular con ocho módulos (ADR-001) | [Estilo arquitectónico](docs/02-arquitectura-software/estilo-arquitectonico.md) |
| Enfoque | Clean Architecture dentro de cada módulo: dominio, aplicación, infraestructura y presentación (ADR-002) | [Enfoque arquitectónico](docs/02-arquitectura-software/enfoque-arquitectonico.md) |
| Componentes | Identidad, Catálogo, Requerimientos, Reglas, Firma digital, Inventario, Auditoría y Reportes | [Componentes](docs/02-arquitectura-software/componentes-arquitectonicos.md) |
| Decisiones | ADR-001 a ADR-013 | [Decisiones arquitectónicas](docs/01-analisis-de-sistema/07-decisiones-arquitectonicas.md) |
| Diseño interno | Capas, clases, estados del requerimiento, SOLID | [Diseño interno](docs/03-diseno-de-software/diseno-interno/diseno-interno-de-modulos.md) · [Principios](docs/03-diseno-de-software/diseno-interno/principios-de-diseno.md) |
| Modelo C4 | Contexto, contenedores, componentes y código | [N1](docs/04-modelo-c4/Nivel1-DiagramadeContextodelSistema.md) · [N2](docs/04-modelo-c4/Nivel2-DiagramadeContenedores.md) · [N3](docs/04-modelo-c4/Nivel3-DiagramadeComponentes.md) · [N4](docs/04-modelo-c4/Nivel4-DiagramadeCodigo.md) |
| Requisitos | 13 historias, 12 requisitos funcionales, 9 atributos de calidad y sus escenarios | [Análisis del sistema](docs/01-analisis-de-sistema/) |

Cómo se llevó esta arquitectura a código: [SOLID y patrones](docs-sprint2/SOLID-y-patrones.md) ·
[Sprint 2: actividades y entregables](docs-sprint2/SPRINT-2.md).

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + TypeScript (Vite), lucide-react |
| Backend | Python + FastAPI, SQLAlchemy, Pydantic, Alembic |
| Firma digital y PDF | `cryptography` (SHA-256 + Ed25519) y ReportLab |
| Base de datos | PostgreSQL 16 |
| Proxy y balanceo | Nginx |
| Contenedores | Docker Compose |
| Pruebas y calidad | pytest + httpx (backend), Jest + Testing Library (frontend), Postman/Newman, k6, Ruff, ESLint |
| CI | GitHub Actions |

## Cómo levantarlo

Requisitos: Docker Desktop con Docker Compose v2. Para correr las pruebas fuera de Docker: Python
3.12 o superior y Node.js 20.

```bash
cd tecnologia
cp .env.example .env                                      # completar los valores; nunca se versiona
python backend/scripts/generar_clave_firma.py >> .env     # clave Ed25519 del sistema
docker compose up --build -d                              # db, api y web
curl -s http://localhost:8080/health
```

Para empezar con la base vacía (solo los seeds): `docker compose down -v && docker compose up -d`.

Guías paso a paso: [quickstart de 001](specs/001-flujo-solicitud/quickstart.md) (flujo
completo) y [quickstart de 002](specs/002-documento-firmado/quickstart.md) (documento y PDF).

### URLs

| Servicio | URL |
|---|---|
| Aplicación web | http://localhost:8080 |
| Swagger UI (OpenAPI) | http://localhost:8080/docs |
| Esquema OpenAPI | http://localhost:8080/openapi.json |
| Salud | http://localhost:8080/health |
| Verificar un PDF (web) | http://localhost:8080/verificar |

### Usuarios de prueba

Todos usan la contraseña que se define en `CONTRASENA_DEMO` del `.env`; esa contraseña no se
versiona.

| Usuario | Rol | Órgano |
|---|---|---|
| `oficial.bim11` | Oficial de logística | Unidad BIM-11 (1DE) |
| `cmdte.bim11` | Comandante de la unidad | Unidad BIM-11 (1DE) |
| `jlog.1de` | Jefe de logística de la Gran Unidad | 1.ª División de Ejército |
| `jalm.sinte` | Jefe de almacén | Almacén de Intendencia |
| `almacenero.sinte` | Almacenero | Almacén de Intendencia |
| `oficial.bim21` · `jlog.2de` | Para probar el aislamiento entre unidades | Unidad y División distintas |
| `auditor` | Auditor (solo consulta y verificación) | Inspectoría General |

## Metodología SDD con Spec Kit

El proyecto se desarrolla con **Spec-Driven Development**: ninguna funcionalidad se programa sin
su especificación aprobada. Se usa [Spec Kit](https://github.com/github/spec-kit) con Claude Code,
y cada incremento sigue el flujo `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`.

- **Constitución:** [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (v1.3.0).
  Fija los principios no negociables (fidelidad a `docs/`, pruebas, seguridad) y registra cada
  desviación aprobada de `docs/` con su motivo.
- Cada incremento tiene su `spec.md` (historias trazadas a HU y RF, criterios de aceptación),
  `plan.md` (revisión de la constitución y desviaciones), `tasks.md` (tareas marcadas al
  completarse), el contrato OpenAPI, el modelo de datos y un quickstart.

| Incremento | Alcance | Especificación |
|---|---|---|
| **001** Flujo de solicitud | Registro y envío; conducto regular con firma Ed25519 por nivel; aprobación del almacén; despacho con bloqueo de stock; acta de recepción firmada; verificación de integridad; línea de tiempo y anulación | [spec](specs/001-flujo-solicitud/spec.md) · [plan](specs/001-flujo-solicitud/plan.md) · [tareas](specs/001-flujo-solicitud/tasks.md) · [OpenAPI](specs/001-flujo-solicitud/contracts/openapi.yaml) |
| **002** Documento firmado y PDF verificable | Documento oficial con sus sellos; revisión obligatoria antes de firmar; PDF firmado con código de verificación; PDF del acta; verificación de un PDF subido (AUTENTICO o ALTERADO) | [spec](specs/002-documento-firmado/spec.md) · [plan](specs/002-documento-firmado/plan.md) · [tareas](specs/002-documento-firmado/tasks.md) · [OpenAPI](specs/002-documento-firmado/contracts/openapi.yaml) |

## Evidencias de calidad

Los escenarios EQ-01 a EQ-09 de
[`docs/`](docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md) se validan con pruebas.
El detalle, con el resultado y si cumple, está en [`evidencias/README.md`](evidencias/README.md).

| Escenario | Resultado | Estado |
|---|---|---|
| EQ-01 Seguridad | 536 de 536 intentos no autorizados rechazados | ✅ |
| EQ-02 Integridad | 11 de 11 alteraciones detectadas; PDF auténtico → AUTENTICO, con un byte cambiado → ALTERADO | ✅ |
| EQ-03 Consistencia del inventario | Despachos simultáneos sin diferencias de stock | ✅ |
| EQ-04 Rendimiento (k6) | p95 de 40,8 ms con caché (objetivo < 2 s) | ✅ |
| EQ-05 Usabilidad | Lighthouse pendiente | ⏳ |
| EQ-06 Disponibilidad | Uptime Kuma pendiente | ⏳ |
| EQ-07 Mantenibilidad | pytest 934 pruebas (97 %), Jest 253 pruebas (100 % de líneas), Ruff y ESLint sin errores | ✅ |
| EQ-08 Trazabilidad | 6 de 6 pasos con usuario, rol, órgano y fecha | ✅ |
| EQ-09 Escalabilidad (k6, 2 instancias) | p95 de 48,2 ms con 40 usuarios | ✅ |
| Estrés hasta 2 000 VU (k6) | Llegó a 2 000 VU; punto de quiebre en unos 80 a 100 VU | ⚠️ |

### Cómo correr las pruebas

```bash
# Backend (requiere DATABASE_URL_TEST en tecnologia/.env y la base de docker compose)
cd tecnologia/backend && ruff check . && pytest --cov

# Frontend
cd tecnologia/frontend && npm run lint && npx tsc --noEmit && npm run test:cov

# API desde fuera del proceso (Postman/Newman)
cd tecnologia/pruebas && npx newman run postman/sga-001.postman_collection.json \
  -e postman/local.postman_environment.json --env-var contrasena=<CONTRASENA_DEMO>
```

El backend se prueba con **pytest** porque es Python (ADR-011); **Jest** se usa en el frontend.
GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)) ejecuta todo en cada push y cada pull
request y publica los reportes de cobertura.

## Estado y pendientes

- [x] Sprint 1: análisis, arquitectura, diseño y modelo C4 (`docs/`).
- [x] Incremento 001: flujo principal de abastecimiento.
- [x] Incremento 002: documento firmado y PDF verificable (cierra la desviación DT-01).
- [ ] HTTPS y despliegue (desviación temporal DT-02, abierta hasta el cierre del Sprint 2).
- [ ] EQ-05 con Lighthouse y EQ-06 con Uptime Kuma.
- [ ] Nivel del COLOGE y aprobación automática.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| [`docs/`](docs/) | Sprint 1: análisis, arquitectura, diseño y C4 (solo lectura) |
| [`docs-sprint2/`](docs-sprint2/) | Sprint 2: actividades y entregables, SOLID y patrones |
| [`specs/`](specs/) | Especificaciones SDD de cada incremento |
| [`tecnologia/`](tecnologia/) | Código: `backend/`, `frontend/`, `nginx/`, `pruebas/` (Postman y k6) y `docker-compose.yml` |
| [`evidencias/`](evidencias/) | Resultados de los escenarios de calidad |
| [`img/`](img/) | Organigrama y diagramas (PNG), con sus fuentes en `img/fuentes-svg/` |
