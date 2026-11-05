# Nivel 2 · Diagrama de contenedores

> **Proyecto:** SGA
> **Modelo:** C4 · Nivel 2 de 4 · **Versión:** 2.0

---

## 1. Objetivo

Abrir la caja «SGA» del nivel 1 y mostrar los **contenedores** que la forman: las aplicaciones y los almacenes de datos que se ejecutan por separado, la tecnología de cada uno y cómo se comunican.

| Aspecto | Descripción |
|---|---|
| Pregunta que responde | ¿De qué piezas ejecutables se compone el sistema y con qué tecnología? |
| Audiencia | Docente y equipo de desarrollo |
| Qué es un contenedor | Algo que se ejecuta o almacena datos de forma independiente: una aplicación web, una API, una base de datos (no es lo mismo que un contenedor Docker) |
| Nivel anterior | `Nivel1-DiagramadeContextodelSistema.md` |
| Siguiente nivel | `Nivel3-DiagramadeComponentes.md` |

---

## 2. Diagrama

![Diagrama de contenedores del SGA](../../img/nivel2-contenedores.png)

> Archivo editable: `img/fuentes-svg/nivel2-contenedores.svg`

---

## 3. Contenedores

| Contenedor | Tecnología | Responsabilidad | Datos que maneja |
|---|---|---|---|
| **Aplicación web** | React + TypeScript | Interfaz responsiva para los ocho roles. Se ejecuta en el navegador | Ninguno permanente; solo el estado de la pantalla |
| **Balanceador de carga** | Nginx | Recibe las peticiones y las reparte entre las instancias de la API (ADR-012) | Ninguno |
| **API SGA** | Python + FastAPI | Expone la API REST y aplica las reglas del negocio: conducto regular, firma, inventario y auditoría. Es un **monolito modular** con Clean Architecture en cada módulo | Ninguno propio; no guarda sesiones (JWT) |
| **Base de datos** | PostgreSQL | Almacena de forma permanente la información del negocio | Órganos, usuarios, almacenes, ítems, stock, requerimientos, firmas, movimientos y auditoría |
| **Almacenamiento de documentos** | Volumen en disco del servidor | Guarda los PDF firmados, que no se modifican | Documentos de cada firma y actas de recepción |
| **Monitoreo** | Uptime Kuma | Revisa el estado de la API y registra caídas y recuperaciones (ADR-013) | Historial de disponibilidad |

---

## 4. Relaciones

| Origen | Destino | Descripción | Protocolo |
|---|---|---|---|
| Personas | Aplicación web | Usan el sistema | HTTPS |
| Aplicación web | Balanceador de carga | Envía las peticiones con el token de sesión | HTTPS / JSON |
| Balanceador de carga | API SGA | Reparte las peticiones entre las instancias | HTTP |
| API SGA | Base de datos | Lee y escribe información en transacciones | SQL |
| API SGA | Almacenamiento de documentos | Guarda y lee los PDF firmados | Sistema de archivos |
| Monitoreo | API SGA | Comprueba que la API responde | HTTP (`/health`) |

> Todos los contenedores se ejecutan con Docker Compose, con reinicio automático (`restart: always`).