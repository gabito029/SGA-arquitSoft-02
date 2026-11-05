# Drivers arquitectónicos

Los **drivers arquitectónicos** identificados para el sistema son los siguientes:

| ID | Driver arquitectónico | Origen | ¿Por qué influye en la arquitectura? | Prioridad |
|---|---|---|---|---|
| DA01 | El sistema debe detectar cualquier alteración de los documentos firmados y del registro de auditoría. | AC02 – Integridad; RC01 – Firma electrónica del sistema | Define el modelo de firma digital, el uso de huellas (hash) y el registro de auditoría encadenado. | Alta |
| DA02 | El stock debe mantenerse consistente aunque varios usuarios operen al mismo tiempo. | AC03 – Consistencia del inventario | Obliga a registrar cada operación de inventario en una sola transacción y a usar un registro de movimientos que no se modifica. | Alta |
| DA03 | Cada usuario solo debe actuar según su rol y el órgano al que pertenece. | AC01 – Seguridad; RC10 – Estructura orgánica | Influye en la autenticación, la autorización por rol y el filtrado de la información según la jerarquía de órganos. | Alta |
| DA04 | Cada requerimiento debe recorrer obligatoriamente los niveles del conducto regular, y cada nivel firma una sola vez. | RC09 – Conducto regular | Define los estados del requerimiento, permite varias firmas por requerimiento y exige reglas que decidan cuándo interviene el COLOGE. | Alta |
| DA05 | El sistema debe ser construido por una sola persona, con especificaciones previas a cada módulo. | RC06 – Desarrollo individual; RC03 – SDD; AC07 – Mantenibilidad | Favorece una aplicación única organizada en módulos con límites claros, que puedan especificarse y construirse uno por uno. | Alta |
| DA06 | Toda firma y decisión debe poder ser consultada por los órganos de control. | AC08 – Trazabilidad; RC11 – Sistema Nacional de Abastecimiento | Influye en el registro del historial de cada nivel y en un rol de solo consulta para el auditor. | Alta |
| DA07 | El sistema debe desarrollarse y ejecutarse sin herramientas de pago. | RC07 – Bajo costo; RC08 – Despliegue con contenedores | Condiciona la elección de tecnologías de código abierto y el despliegue con Docker Compose. | Media |
| DA08 | El sistema debe ser una aplicación web usable desde un celular, comunicada con el backend mediante una API REST. | AC05 – Usabilidad; RC02 – Aplicación web responsiva; RC05 – API REST | Influye en una interfaz responsiva separada del backend y en formularios con pocos campos. | Media |
| DA09 | El sistema debe responder rápido, recuperarse ante fallas y poder crecer agregando instancias. | AC04 – Rendimiento; AC06 – Disponibilidad; AC09 – Escalabilidad | Obliga a que la API no guarde estado de sesión, a usar un balanceador de carga y a configurar el reinicio automático de los contenedores. | Media |

---
