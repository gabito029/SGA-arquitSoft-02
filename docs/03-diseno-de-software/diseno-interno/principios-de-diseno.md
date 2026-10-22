# Principios de diseño (SOLID)

## Objetivo

Documentar cómo se aplican los principios SOLID en el backend del SGA, organizado en capas por módulo, para que cada módulo se programe de forma uniforme y las reglas del negocio no dependan de la tecnología.

## Contexto

- **Estilo:** monolito modular (Python + FastAPI).
- **Enfoque interno:** capas por módulo (API, servicio, repositorio, modelos).
- **Módulo de referencia:** Solicitudes, porque coordina las reglas, la firma, el inventario, los mensajes y la auditoría.

## SOLID en el módulo Solicitudes

| Principio | Dónde se aplica (capa) | Cómo se cumple en el SGA | Archivos |
|---|---|---|---|
| **S** · Responsabilidad única | Todas las capas | Cada archivo tiene una sola tarea: la API recibe la petición, el servicio aplica las reglas, el repositorio consulta la base de datos y los modelos definen las tablas. | `api.py`, `service.py`, `repository.py`, `models.py` |
| **O** · Abierto/cerrado | Firma digital | Para guardar los PDF en otro almacenamiento se crea un nuevo adaptador; el módulo de firma no se modifica. | `core/storage.py` |
| **L** · Sustitución de Liskov | Firma digital | El almacenamiento local y cualquier otro cumplen el mismo contrato, por lo que se pueden intercambiar sin errores. | `core/storage.py` |
| **I** · Segregación de interfaces | Entre módulos | Cada módulo ofrece solo las funciones que los demás necesitan; por ejemplo, Inventario ofrece la consulta del nivel de stock. | `modules/*/service.py` |
| **D** · Inversión de dependencias | Firma digital y API | La firma depende de la interfaz de almacenamiento, no del disco; las rutas reciben la conexión y el usuario mediante inyección de dependencias. | `core/storage.py`, `core/security.py` |

## Reglas para programar

1. No colocar reglas del negocio en las rutas de la API.
2. Un módulo nunca usa el repositorio ni los modelos de otro módulo.
3. Toda operación que modifica el stock se realiza dentro de una sola transacción.
4. No programar criptografía propia: se usan librerías reconocidas.