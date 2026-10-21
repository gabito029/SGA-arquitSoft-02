# Atributos de calidad

| ID | Atributo de calidad | Escenario de calidad |
|---|---|---|
| AC01 | **Seguridad** | Solo los usuarios con el rol y el almacén autorizados pueden firmar, despachar o confirmar recepciones; las contraseñas se almacenan cifradas y la comunicación se realiza por HTTPS. |
| AC02 | **Integridad** | Cualquier alteración de un documento firmado, de los datos firmados o del registro de auditoría debe ser detectada al verificarlos. |
| AC03 | **Consistencia del inventario** | El stock de cada ítem debe coincidir siempre con la suma de sus movimientos, incluso cuando varios usuarios operan al mismo tiempo. |
| AC04 | **Rendimiento** | Las operaciones habituales y el panel de control deben responder rápidamente con la carga normal de trabajo de los almacenes. |
| AC05 | **Usabilidad** | El registro de una solicitud debe ser corto y sencillo, y el sistema debe poder usarse desde una computadora o un celular. |
| AC06 | **Disponibilidad** | El sistema debe recuperarse automáticamente ante una falla y permitir comprobar su estado de funcionamiento. |
| AC07 | **Mantenibilidad** | El sistema debe estar organizado en módulos independientes, de modo que un cambio en una funcionalidad no afecte innecesariamente a las demás. |