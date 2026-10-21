# Requisitos funcionales

## Requisitos funcionales

| ID | Requisito funcional |
|---|---|
| RF01 | El sistema debe permitir iniciar sesión y controlar el acceso según el rol y el almacén del usuario. |
| RF02 | El sistema debe permitir registrar solicitudes de salida y de reposición mediante un formulario corto. |
| RF03 | El sistema debe decidir, mediante reglas configurables, si una solicitud se aprueba automáticamente o requiere firma. |
| RF04 | El sistema debe permitir firmar digitalmente la aprobación de una solicitud y generar un documento PDF verificable. |
| RF05 | El sistema debe registrar el despacho de un pedido con las cantidades enviadas por ítem. |
| RF06 | El sistema debe permitir confirmar la recepción de un pedido con un acta firmada, registrando las diferencias. |
| RF07 | El sistema debe mostrar el seguimiento de cada pedido con su línea de tiempo. |
| RF08 | El sistema debe controlar el inventario mediante un registro de movimientos que no se puede modificar. |
| RF09 | El sistema debe generar alertas cuando el stock de un ítem esté por debajo de su umbral. |
| RF10 | El sistema debe sugerir cantidades de reposición a partir de las alertas de stock. |
| RF11 | El sistema debe calcular automáticamente la prioridad de cada solicitud y ordenar las solicitudes pendientes. |
| RF12 | El sistema debe permitir enviar mensajes dentro de una solicitud y notificar a los usuarios involucrados. |
| RF13 | El sistema debe permitir registrar, actualizar y desactivar almacenes, ítems, usuarios y reglas de aprobación. |
| RF14 | El sistema debe verificar si un documento firmado o el registro de auditoría fueron alterados. |
| RF15 | El sistema debe mostrar un panel de control y generar reportes exportables en formato CSV. |

---

## Relación entre historias de usuario y requisitos funcionales

| Historia de usuario | Requisitos funcionales relacionados |
|---|---|
| HU01 Iniciar sesión según rol | RF01 |
| HU02 Registrar solicitud | RF02 |
| HU03 Aprobación automática | RF03 |
| HU04 Firmar o rechazar | RF04 |
| HU05 Despachar pedido | RF05 |
| HU06 Confirmar recepción | RF06, RF08 |
| HU07 Ver línea de tiempo | RF07 |
| HU08 Alertas y sugerencias | RF09, RF10 |
| HU09 Atender por prioridad | RF11 |
| HU10 Mensajes y notificaciones | RF12 |
| HU11 Gestionar maestros y reglas | RF13 |
| HU12 Verificar documentos y auditoría | RF14 |
| HU13 Panel y reportes | RF15 |