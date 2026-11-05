# Principios de diseño (SOLID)

## Objetivo

Documentar cómo se aplican los principios SOLID en el backend del SGA, organizado con Clean Architecture, para que cada módulo se programe de forma uniforme y las reglas del negocio no dependan de la tecnología.

## Contexto

- **Estilo:** monolito modular (Python + FastAPI).
- **Enfoque interno:** Clean Architecture (dominio, aplicación, infraestructura y presentación).
- **Módulo de referencia:** Requerimientos, porque concentra el conducto regular, la firma digital y la relación con el inventario.

## SOLID en el módulo Requerimientos

| Principio | Dónde se aplica (capa) | Cómo se cumple en el SGA | Archivos |
|---|---|---|---|
| **S** · Responsabilidad única | Todas las capas | La ruta recibe la petición, el caso de uso coordina la firma, la entidad aplica las reglas del conducto regular y el repositorio guarda en PostgreSQL. | `router.py`, `firmar_requerimiento.py`, `requerimiento.py`, `repositorio_postgres.py` |
| **O** · Abierto/cerrado | Infraestructura | Para guardar los PDF en otro lugar se crea un nuevo adaptador de `AlmacenDocumentos`; el caso de uso no se modifica. | `almacen_documentos_disco.py` |
| **L** · Sustitución de Liskov | Infraestructura | Cualquier adaptador que cumpla el puerto `FirmadorDocumentos` puede reemplazar a `FirmadorEd25519` sin errores; en las pruebas se usa uno falso. | `firmador_ed25519.py` |
| **I** · Segregación de interfaces | Dominio | Cada puerto es pequeño y tiene un solo propósito: repositorio, firmador, almacén de documentos y auditoría, en lugar de una interfaz gigante. | `dominio/puertos.py` |
| **D** · Inversión de dependencias | Aplicación y dominio | El caso de uso depende de los puertos del dominio, no de PostgreSQL ni de `cryptography`; la raíz de composición inyecta los adaptadores. | `firmar_requerimiento.py`, `dependencias.py`, `main.py` |

## Qué pasaría sin SOLID en el SGA

| Sin el principio | Consecuencia |
|---|---|
| S | La ruta de la API firmaría, guardaría y validaría a la vez: un error en una parte afectaría a todo. |
| O | Cambiar el almacenamiento de los PDF obligaría a modificar los casos de uso ya probados. |
| L | Un adaptador distinto podría romper la firma sin que el resto del sistema lo note. |
| I | Cada adaptador tendría que implementar métodos que no usa. |
| D | Las reglas del conducto regular no podrían probarse sin una base de datos. |

## Reglas para programar

1. El dominio no importa FastAPI, SQLAlchemy ni `cryptography`.
2. Un módulo nunca usa el repositorio ni las tablas de otro módulo; usa su servicio público.
3. Toda operación que firma o modifica el stock se realiza dentro de una sola transacción.
4. No programar criptografía propia: se usa la librería `cryptography`.