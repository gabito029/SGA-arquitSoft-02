# Patrones de diseño

## Objetivo

Documentar los patrones de diseño aplicados en el backend del SGA, indicando dónde se usan, qué problema resuelven y con qué tecnología se implementan, para programar todos los módulos de forma uniforme.

## Contexto

- **Estilo:** monolito modular (Python + FastAPI).
- **Enfoque interno:** capas por módulo (API, servicio, repositorio, modelos).
- **Base:** diagrama de componentes (C4 nivel 3).

## Patrones aplicados

| Patrón | Dónde se usa | Problema que resuelve | Se implementa con | Archivos en el código |
|---|---|---|---|---|
| Repository | Todos los módulos → Base de datos | El servicio no debe escribir consultas SQL | SQLAlchemy | `modules/*/repository.py` |
| Adapter | Firma digital → Almacenamiento de documentos | Guardar los PDF en el disco local o en otro almacenamiento sin cambiar el módulo de firma | Interfaz `ObjectStorage` | `core/storage.py` |
| State | Solicitudes | Impedir cambios de estado no permitidos | Tabla de transiciones permitidas | `modules/requests/service.py` |
| Chain of Responsibility | Reglas | Evaluar las reglas en orden; decide la primera que coincide | Lista de reglas ordenada | `modules/rules/service.py` |
| Unit of Work | Operaciones que modifican el stock | Guardar estado, firma, movimientos, alertas y auditoría juntos | Sesión y transacción de SQLAlchemy | `modules/requests/service.py` |
| Dependency Injection | API de todos los módulos | Entregar a cada ruta la conexión a la base de datos y el usuario actual | `Depends` de FastAPI | `core/database.py`, `core/security.py` |

## Cómo funciona cada patrón

| Patrón | En pocas palabras |
|---|---|
| Repository | El servicio dice `obtener(solicitud)`; el repositorio escribe la consulta. |
| Adapter | La firma dice `guardar(pdf)`; el adaptador decide si lo guarda en el disco o en otro servicio. |
| State | Antes de cambiar el estado, se verifica si el cambio está permitido; si no lo está, se rechaza. |
| Chain of Responsibility | Se recorren las reglas activas en orden; la primera que coincide decide. Si ninguna coincide, se exige firma. |
| Unit of Work | Todo ocurre dentro de una transacción; si un paso falla, no se guarda nada. |
| Dependency Injection | FastAPI entrega lo que cada ruta necesita, y en las pruebas se puede reemplazar fácilmente. |

## Beneficio

- Cambiar el lugar donde se guardan los PDF solo afecta al adaptador.
- Las reglas de aprobación y los cambios de estado se pueden probar sin base de datos.
- El inventario nunca queda a medias aunque falle un paso intermedio.