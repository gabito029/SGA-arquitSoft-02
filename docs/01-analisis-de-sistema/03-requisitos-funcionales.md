# Requisitos funcionales

## Requisitos funcionales

| ID | Requisito funcional |
|---|---|
| RF01 | El sistema debe permitir iniciar sesión y controlar el acceso según el rol del usuario y el órgano al que pertenece. |
| RF02 | El sistema debe permitir registrar requerimientos de materiales y salidas del almacén de la unidad mediante un formulario corto. |
| RF03 | El sistema debe decidir, mediante reglas configurables, si un requerimiento necesita la autorización del COLOGE y si se aprueba automáticamente en el almacén o requiere la firma del jefe de almacén. |
| RF04 | El sistema debe permitir firmar digitalmente cada paso del conducto regular (visto bueno, conformidad, autorización y aprobación) y generar un documento PDF verificable. |
| RF05 | El sistema debe registrar el despacho de un requerimiento con las cantidades enviadas por ítem. |
| RF06 | El sistema debe permitir confirmar la recepción de un requerimiento con un acta firmada, registrando las diferencias. |
| RF07 | El sistema debe mostrar el seguimiento de cada requerimiento con su línea de tiempo y las firmas de cada nivel. |
| RF08 | El sistema debe controlar el inventario de cada almacén mediante un registro de movimientos que no se puede modificar. |
| RF09 | El sistema debe generar alertas cuando el stock de un ítem esté por debajo de su umbral. |
| RF10 | El sistema debe sugerir un requerimiento con las cantidades necesarias a partir de las alertas de stock de una unidad. |
| RF11 | El sistema debe calcular automáticamente la prioridad de cada requerimiento y ordenar los requerimientos pendientes. |
| RF12 | El sistema debe permitir enviar mensajes dentro de un requerimiento y notificar a los usuarios involucrados. |
| RF13 | El sistema debe permitir registrar, actualizar y desactivar órganos, unidades, almacenes, ítems, usuarios y reglas de aprobación, respetando la estructura orgánica del Ejército. |
| RF14 | El sistema debe verificar si un documento firmado o el registro de auditoría fueron alterados. |
| RF15 | El sistema debe mostrar un panel de control y generar reportes exportables en formato CSV. |
| RF16 | El sistema debe enviar cada requerimiento por los niveles del conducto regular (unidad, gran unidad, COLOGE cuando corresponda y almacén) sin permitir omitir ningún nivel. |
| RF17 | El sistema debe permitir que cualquier firmante rechace un requerimiento indicando el motivo, y notificar al solicitante. |
| RF18 | El sistema debe permitir al auditor consultar la trazabilidad de los requerimientos sin poder modificarlos. |

---

## Relación entre historias de usuario y requisitos funcionales

| Historia de usuario | Requisitos funcionales relacionados |
|---|---|
| HU01 Iniciar sesión según rol y órgano | RF01 |
| HU02 Registrar requerimiento | RF02, RF16 |
| HU03 Registrar salidas | RF02, RF08 |
| HU04 Visto bueno del comandante | RF04, RF16, RF17 |
| HU05 Conformidad de la gran unidad | RF04, RF16, RF17 |
| HU06 Autorización del COLOGE | RF03, RF04, RF17 |
| HU07 Aprobación del almacén | RF04, RF17 |
| HU08 Aprobación automática | RF03 |
| HU09 Despachar requerimiento | RF05 |
| HU10 Confirmar recepción | RF06, RF08 |
| HU11 Ver línea de tiempo | RF07 |
| HU12 Alertas y sugerencias | RF09, RF10 |
| HU13 Atender por prioridad | RF11 |
| HU14 Mensajes y notificaciones | RF12 |
| HU15 Gestionar estructura y reglas | RF13 |
| HU16 Auditoría y verificación | RF14, RF18 |
| HU17 Panel y reportes | RF15 |