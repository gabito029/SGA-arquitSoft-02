# Sistema de Gestión Digital de Almacén con Firma Digital (SGA)

## Nombre
Rodrigo Cutipa, Gabriela Ana

## Descripción
Aplicación web académica para gestionar los requerimientos de materiales de las unidades del **Ejército del Perú** a sus almacenes.
Reemplaza los oficios en papel y las firmas físicas por requerimientos digitales que recorren el **conducto regular**
(unidad, gran unidad, COLOGE cuando corresponde y almacén), con **firma digital** en cada nivel, control de inventario,
alertas de stock bajo y seguimiento de cada requerimiento hasta su recepción.

Es un proyecto individual desarrollado con **Spec-Driven Development (SDD)**: primero se redactan las especificaciones
de cada módulo y luego se genera el código con apoyo de inteligencia artificial (Claude Code).

## Problema
En la logística del Ejército todavía se depende del papel y existen trámites innecesarios: cada requerimiento exige
oficios con firmas físicas en cada nivel, no hay visibilidad del estado de un pedido y no existe un sistema único
para controlar los inventarios en tiempo real.

## Caso de estudio
Comando Logístico del Ejército (COLOGE), Servicio de Intendencia y unidades de las Divisiones de Ejército.

## Curso
IS488 Arquitectura de Software — Universidad Nacional de San Cristóbal de Huamanga (UNSCH)

## Docente
Ing. Lizbeth Jaico Quispe

---

## Módulos funcionales
1. **Identidad**: inicio de sesión, roles y acceso según el órgano.
2. **Catálogo**: órganos, unidades, almacenes, ítems y usuarios.
3. **Requerimientos**: registro, conducto regular, recepción y línea de tiempo (módulo núcleo).
4. **Reglas**: autorización del COLOGE y aprobación automática.
5. **Firma digital**: firma Ed25519, PDF y verificación.
6. **Inventario**: stock, movimientos, despachos, salidas y alertas.
7. **Auditoría**: registro encadenado y verificación.
8. **Reportes**: panel de control.

## Tecnologías previstas
| Capa | Tecnología |
|---|---|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI (monolito modular con Clean Architecture) |
| Base de datos | PostgreSQL |
| Firma digital | Librería `cryptography` (SHA-256 y Ed25519) |
| Balanceo de carga | Nginx |
| Contenedores | Docker Compose |
| Pruebas y calidad | pytest, Locust, Google Lighthouse, Uptime Kuma, Ruff |

---

## Contenido del repositorio

### 01 · Análisis del sistema
| Documento | Descripción |
|---|---|
| [Contexto organizacional](docs/01-analisis-de-sistema/00-contexto-organizacional.md) | Organigrama del Ejército del Perú y órganos relacionados |
| [Actores](docs/01-analisis-de-sistema/01-actores.md) | Ocho roles del sistema y su órgano |
| [Historias de usuario](docs/01-analisis-de-sistema/02-historias-de-usuario.md) | 13 historias de usuario |
| [Requisitos funcionales](docs/01-analisis-de-sistema/03-requisitos-funcionales.md) | 12 requisitos y su relación con las historias |
| [Atributos de calidad](docs/01-analisis-de-sistema/04-atributos-de-calidad.md) | 9 atributos de calidad |
| [Restricciones](docs/01-analisis-de-sistema/05-restricciones.md) | Restricciones del docente, del contexto y normativas |
| [Drivers arquitectónicos](docs/01-analisis-de-sistema/06-drivers-arquitectonicos.md) | Factores que guían la arquitectura |
| [Decisiones arquitectónicas](docs/01-analisis-de-sistema/07-decisiones-arquitectonicas.md) | ADR-001 a ADR-013 |
| [Escenarios de calidad](docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md) | Escenarios medibles con tipo de prueba y herramienta |

### 02 · Arquitectura de software
| Documento | Descripción |
|---|---|
| [Arquitectura inicial](docs/02-arquitectura-software/arquitectura-inicial.md) | Vista general por capas |
| [Estilo arquitectónico](docs/02-arquitectura-software/estilo-arquitectonico.md) | Monolito modular |
| [Enfoque arquitectónico](docs/02-arquitectura-software/enfoque-arquitectonico.md) | Clean Architecture dentro de cada módulo |
| [Componentes arquitectónicos](docs/02-arquitectura-software/componentes-arquitectonicos.md) | Ocho módulos e infraestructura |

### 03 · Diseño de software
| Documento | Descripción |
|---|---|
| [Diseño interno de módulos](docs/03-diseno-de-software/diseno-interno/diseno-interno-de-modulos.md) | Paquetes, clases, estados y secuencia del módulo Requerimientos |
| [Patrones de diseño](docs/03-diseno-de-software/diseno-interno/patrones-de-diseno.md) | Patrones aplicados en el backend |
| [Principios de diseño](docs/03-diseno-de-software/diseno-interno/principios-de-diseno.md) | Aplicación de SOLID |

### 04 · Modelo C4
| Documento | Descripción |
|---|---|
| [Nivel 1 · Contexto](docs/04-modelo-c4/Nivel1-DiagramadeContextodelSistema.md) | El sistema, sus usuarios y su entorno |
| [Nivel 2 · Contenedores](docs/04-modelo-c4/Nivel2-DiagramadeContenedores.md) | Aplicación web, Nginx, API, base de datos, documentos y monitoreo |
| [Nivel 3 · Componentes](docs/04-modelo-c4/Nivel3-DiagramadeComponentes.md) | Módulos de la API |
| [Nivel 4 · Código](docs/04-modelo-c4/Nivel4-DiagramadeCodigo.md) | Clases y secuencia de firma del conducto regular |

### Otras carpetas
- `img/`: organigrama y diagramas exportados (PNG), con sus fuentes editables en `img/fuentes-svg/`.
- `tecnologia/`: código base del sistema (siguiente sprint).

---

## Estado del proyecto
- [x] Estructura del repositorio
- [x] Sprint 1: análisis, arquitectura, diseño y modelo C4
- [x] Especificación SDD del incremento 001 (`specs/001-flujo-solicitud/`)
- [x] Incremento 001, flujo principal de abastecimiento (rama `001-flujo-solicitud`):
  registro y envío, conducto regular con firma Ed25519, aprobación del almacén y despacho con
  bloqueo de stock, acta de recepción con verificación de integridad, línea de tiempo y anulación.
  Evidencias de EQ-01, EQ-02, EQ-03, EQ-07 y EQ-08 en `evidencias/`.
- [ ] Incremento 002 (Sprint 2): nivel del COLOGE, PDF verificable (DT-01), HTTPS y despliegue
  (DT-02), y las corridas de carga y estrés con k6 (EQ-04, EQ-09, 2 000 usuarios).

## Cómo ejecutar
Requisitos: Docker Desktop con Docker Compose v2. La guía completa, con los usuarios de prueba y
la demo paso a paso, está en
[specs/001-flujo-solicitud/quickstart.md](specs/001-flujo-solicitud/quickstart.md).

```bash
cd tecnologia
cp .env.example .env                                      # completar los valores; nunca se versiona
python backend/scripts/generar_clave_firma.py >> .env     # clave Ed25519 de la firma
docker compose up --build -d
```

| Servicio | URL |
|---|---|
| Aplicación web | http://localhost:8080 |
| Swagger UI | http://localhost:8080/docs |
| Salud | http://localhost:8080/health |

Pruebas: `ruff check . && pytest --cov` en `tecnologia/backend` (requiere `DATABASE_URL_TEST`),
`npm run lint && npx tsc --noEmit && npm run test:cov` en `tecnologia/frontend`, y la colección
de Postman en `tecnologia/pruebas/postman/` con Newman.