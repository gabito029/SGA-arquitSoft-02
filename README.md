# Sistema de Gestión Digital de Almacén con Firma Digital (SGA)

## Nombre
Rodrigo Cutipa, Gabriela Ana

## Descripción
Aplicación web académica para gestionar solicitudes de materiales de almacén.
Reemplaza los oficios en papel y las firmas físicas por solicitudes digitales cortas,
aprobadas mediante reglas y firmadas digitalmente, con control de inventario,
alertas de stock bajo y seguimiento de cada pedido hasta su recepción.

## Problema
Las solicitudes de almacén pasan por verificaciones repetidas y requieren documentación
extensa con firmas físicas. No existe visibilidad del estado de un pedido, los materiales
se agotan sin aviso y no hay un criterio claro para decidir qué pedido atender primero.

## Caso de estudio
Almacenes de una organización que se abastecen entre sí y de proveedores externos.

## Curso
IS488 Arquitectura de Software — Universidad Nacional de San Cristóbal de Huamanga (UNSCH)

## Docente
Ing. Lizbeth Jaico Quispe

---

## Contenido del repositorio

### 01 · Análisis del sistema
| Documento | Descripción |
|---|---|
| [Actores](docs/01-analisis-de-sistema/01-actores.md) | Usuarios y participantes del sistema |
| [Historias de usuario](docs/01-analisis-de-sistema/02-historias-de-usuario.md) | Necesidades de cada actor |
| [Requisitos funcionales](docs/01-analisis-de-sistema/03-requisitos-funcionales.md) | Funciones del sistema y relación con las historias |
| [Atributos de calidad](docs/01-analisis-de-sistema/04-atributos-de-calidad.md) | Seguridad, integridad, consistencia y otros |
| [Restricciones](docs/01-analisis-de-sistema/05-restricciones.md) | Condiciones que limitan el diseño |
| [Drivers arquitectónicos](docs/01-analisis-de-sistema/06-drivers-arquitectonicos.md) | Factores que guían la arquitectura |
| [Decisiones arquitectónicas](docs/01-analisis-de-sistema/07-decisiones-arquitectonicas.md) | ADR-001 a ADR-009 |
| [Escenarios de calidad](docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md) | Escenarios medibles por atributo |

### 02 · Arquitectura de software
| Documento | Descripción |
|---|---|
| [Arquitectura inicial](docs/02-arquitectura-software/arquitectura-inicial.md) | Vista general por capas |
| [Estilo arquitectónico](docs/02-arquitectura-software/estilo-arquitectonico.md) | Monolito modular + capas |
| [Enfoque arquitectónico](docs/02-arquitectura-software/enfoque-arquitectonico.md) | Capas dentro de cada módulo |
| [Componentes arquitectónicos](docs/02-arquitectura-software/componentes-arquitectonicos.md) | Los nueve módulos y sus relaciones |

### 03 · Diseño de software
| Documento | Descripción |
|---|---|
| [Diseño interno de módulos](docs/03-diseno-de-software/diseno-interno/diseno-interno-de-modulos.md) | Estructura de código del módulo Solicitudes |
| [Patrones de diseño](docs/03-diseno-de-software/diseno-interno/patrones-de-diseno.md) | Patrones aplicados en el backend |
| [Principios de diseño](docs/03-diseno-de-software/diseno-interno/principios-de-diseno.md) | Aplicación de SOLID |

### 04 · Modelo C4
| Documento | Descripción |
|---|---|
| [Nivel 1 · Contexto](docs/04-modelo-c4/Nivel1-DiagramadeContextodelSistema.md) | El sistema, sus usuarios y su entorno |
| [Nivel 2 · Contenedores](docs/04-modelo-c4/Nivel2-DiagramadeContenedores.md) | Aplicación web, API, base de datos y documentos |
| [Nivel 3 · Componentes](docs/04-modelo-c4/Nivel3-DiagramadeComponentes.md) | Módulos de la API |
| [Nivel 4 · Código](docs/04-modelo-c4/Nivel4-DiagramadeCodigo.md) | Clases y secuencia de aprobación |

---

## Tecnologías previstas
Python · FastAPI · PostgreSQL · React · TypeScript · Docker Compose

## Estado
**Sprint 1:** análisis, arquitectura y diseño documentados.