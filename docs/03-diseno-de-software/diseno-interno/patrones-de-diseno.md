# Patrones de diseño

## Objetivo

Documentar los patrones de diseño aplicados en el backend del SGA, indicando dónde se usan, qué problema resuelven y con qué tecnología se implementan, para programar todos los módulos de forma uniforme.

## Contexto

- **Estilo:** monolito modular (Python + FastAPI).
- **Enfoque interno:** Clean Architecture (dominio, aplicación, infraestructura y presentación).
- **Base:** diagrama de componentes (C4 nivel 3).

## Patrones aplicados

| Patrón | Dónde se usa | Problema que resuelve | Se implementa con | Archivos en el código |
|---|---|---|---|---|
| Repository | Todos los módulos → PostgreSQL | El dominio y los casos de uso no deben escribir consultas SQL | Puerto en el dominio y adaptador con SQLAlchemy | `dominio/puertos.py`, `infraestructura/repositorio_postgres.py` |
| Adapter | Firma digital y almacenamiento de documentos | La firma y el guardado del PDF dependen de librerías externas | Puertos `FirmadorDocumentos` y `AlmacenDocumentos` con sus adaptadores | `infraestructura/firmador_ed25519.py`, `infraestructura/almacen_documentos_disco.py` |
| State | Requerimientos | Impedir que un requerimiento salte o repita niveles del conducto regular | Tabla de transiciones permitidas en la entidad | `dominio/requerimiento.py`, `dominio/estado.py` |
| Chain of Responsibility | Reglas | Evaluar las reglas en orden para decidir si interviene el COLOGE o si hay aprobación automática | Lista ordenada de reglas | `dominio/regla_aprobacion.py` |
| Unit of Work | Operaciones que firman o modifican el stock | Guardar estado, firma, movimientos y auditoría juntos | Sesión y transacción de SQLAlchemy | `infraestructura/repositorio_postgres.py` |
| Dependency Injection | Raíz de composición y rutas | Decidir en un solo lugar qué adaptador implementa cada puerto | `Depends` de FastAPI | `main.py`, `infraestructura/dependencias.py` |

## Cómo funciona cada patrón

| Patrón | En pocas palabras |
|---|---|
| Repository | El caso de uso dice `guardar(requerimiento)`; el repositorio escribe el SQL. |
| Adapter | El caso de uso dice `firmar(contenido)`; el adaptador usa la librería `cryptography`. |
| State | Antes de cambiar el estado, la entidad verifica si el nivel que firma es el que corresponde; si no, rechaza la operación. |
| Chain of Responsibility | Se revisan las reglas en orden: material de guerra o monto alto → COLOGE; bajo riesgo → aprobación automática; en otro caso → firma del jefe de almacén. |
| Unit of Work | Todo ocurre dentro de una transacción; si un paso falla, no se guarda nada. |
| Dependency Injection | FastAPI entrega a cada ruta el caso de uso ya armado con sus adaptadores, y en las pruebas se pueden reemplazar por versiones falsas. |

## Beneficio

- Cambiar dónde se guardan los PDF o cómo se firma solo afecta a un adaptador.
- Las reglas del conducto regular se prueban sin base de datos.
- El inventario nunca queda a medias aunque falle un paso intermedio.

## Patrones previstos para siguientes iteraciones

| Patrón | Dónde se aplicaría | Cuándo |
|---|---|---|
| Observer | Avisar a los usuarios cuando un requerimiento cambia de estado | Fase 2, con el módulo de Mensajería |
| Decorator | Agregar caché a las consultas frecuentes de ítems sin modificar el repositorio | Si aumenta la carga de usuarios |