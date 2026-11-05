# Requisitos funcionales

## Requisitos funcionales

| ID | Requisito funcional |
|---|---|
| RF01 | El sistema debe permitir iniciar sesión y controlar el acceso según el rol del usuario y el órgano al que pertenece. |
| RF02 | El sistema debe permitir registrar requerimientos de materiales mediante un formulario corto. |
| RF03 | El sistema debe enviar cada requerimiento por los niveles del conducto regular sin permitir omitir ningún nivel, y permitir que cualquier firmante lo rechace indicando el motivo. |
| RF04 | El sistema debe decidir, mediante reglas definidas en su configuración, si un requerimiento necesita la autorización del COLOGE y si se aprueba automáticamente en el almacén. |
| RF05 | El sistema debe firmar digitalmente cada paso del conducto regular y el acta de recepción, generar un documento PDF y verificar si fue alterado. |
| RF06 | El sistema debe registrar los despachos y las salidas de cada almacén mediante un registro de movimientos que no se puede modificar. |
| RF07 | El sistema debe permitir confirmar la recepción de un requerimiento con un acta firmada, registrando las diferencias. |
| RF08 | El sistema debe mostrar el seguimiento de cada requerimiento con su línea de tiempo y las firmas de cada nivel. |
| RF09 | El sistema debe generar alertas cuando el stock de un ítem esté por debajo de su umbral. |
| RF10 | El sistema debe permitir registrar, actualizar y desactivar órganos, unidades, almacenes, ítems y usuarios. |
| RF11 | El sistema debe registrar las operaciones en una auditoría encadenada y permitir al auditor verificar su integridad y consultar la trazabilidad. |
| RF12 | El sistema debe mostrar un panel de control con el estado de los requerimientos y del stock. |

---

## Relación entre historias de usuario y requisitos funcionales

| Historia de usuario | Requisitos funcionales relacionados |
|---|---|
| HU01 Iniciar sesión según rol y órgano | RF01 |
| HU02 Registrar y seguir un requerimiento | RF02, RF08 |
| HU03 Visto bueno y conformidad | RF03, RF05 |
| HU04 Autorización del COLOGE | RF03, RF04, RF05 |
| HU05 Aprobación del almacén | RF03, RF05 |
| HU06 Aprobación automática | RF04 |
| HU07 Despachar requerimiento | RF06 |
| HU08 Confirmar recepción | RF05, RF07 |
| HU09 Registrar salidas | RF06 |
| HU10 Alertas de stock | RF09 |
| HU11 Gestionar estructura orgánica | RF10 |
| HU12 Auditoría y verificación | RF05, RF11 |
| HU13 Panel de control | RF12 |