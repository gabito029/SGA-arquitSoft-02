# Drivers arquitectónicos

Los **drivers arquitectónicos** identificados para el sistema son los siguientes:

| ID | Driver arquitectónico | Origen | ¿Por qué influye en la arquitectura? |
|---|---|---|---|
| DA01 | El sistema debe detectar cualquier alteración de los documentos firmados y del registro de auditoría. | AC02 – Integridad | Define el modelo de firma digital, el uso de huellas (hash) y el registro de auditoría encadenado. |
| DA02 | El stock debe mantenerse consistente aunque varios usuarios operen al mismo tiempo. | AC03 – Consistencia del inventario | Obliga a registrar cada operación de inventario en una sola transacción y a usar un registro de movimientos que no se modifica. |
| DA03 | Cada usuario solo debe actuar según su rol y su almacén. | AC01 – Seguridad | Influye en la autenticación, la autorización por rol y el filtrado de la información por almacén. |
| DA04 | El sistema debe poder ser construido y mantenido por una sola persona. | RC04 – Desarrollo individual; AC07 – Mantenibilidad | Favorece una aplicación única organizada en módulos, en lugar de varios servicios distribuidos. |
| DA05 | El sistema debe desarrollarse y ejecutarse sin herramientas de pago. | RC05 – Bajo costo; RC07 – Despliegue con contenedores | Condiciona la elección de tecnologías de código abierto y el despliegue con Docker Compose. |
| DA06 | El frontend y el backend deben comunicarse mediante una API REST. | RC03 – API REST | Limita las alternativas de comunicación entre las partes del sistema. |
| DA07 | El registro de solicitudes debe ser rápido y usable desde un celular. | AC05 – Usabilidad; RC01 – Aplicación web responsiva | Influye en el diseño de una interfaz responsiva y en que el sistema calcule automáticamente datos como la prioridad. |