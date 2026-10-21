# Escenarios de atributos de calidad del SGA

## EQ-01. Seguridad: acción no autorizada

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Seguridad (AC01) |
| **Fuente** | Usuario con rol de almacenero |
| **Estímulo** | Intenta firmar la aprobación de una solicitud o confirmar la recepción de un pedido. |
| **Condición** | El usuario inició sesión correctamente. |
| **Respuesta esperada** | El sistema rechaza la acción e informa que no tiene permiso. Si la solicitud pertenece a otro almacén, responde como si no existiera. |
| **Medida** | **Propuesta por validar:** el 100 % de los intentos no autorizados son rechazados. |
| **Verificación** | Ejecutar pruebas automáticas de autorización por rol y por almacén. |
| **Estado** | Pendiente de implementar el módulo de identidad. |

## EQ-02. Integridad: documento alterado

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Integridad (AC02) |
| **Fuente** | Persona que modifica un documento firmado o un dato en la base de datos |
| **Estímulo** | Se cambia el contenido del PDF firmado o un valor de la solicitud aprobada. |
| **Condición** | La solicitud fue aprobada y su documento fue firmado. |
| **Respuesta esperada** | Al verificar el documento, el sistema indica que fue **alterado**. |
| **Medida** | **Propuesta por validar:** el 100 % de las alteraciones son detectadas. |
| **Verificación** | Ejecutar pruebas que modifican un byte del PDF y un dato firmado, y comprobar el resultado de la verificación. |
| **Estado** | Pendiente de implementar el módulo de firma. |

## EQ-03. Consistencia del inventario: despachos simultáneos

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Consistencia del inventario (AC03) |
| **Fuente** | Dos usuarios del almacén de origen |
| **Estímulo** | Despachan al mismo tiempo dos pedidos cuyas cantidades juntas superan el stock disponible. |
| **Condición** | Ambos pedidos están aprobados. |
| **Respuesta esperada** | Solo uno de los despachos se registra; el otro es rechazado sin dejar cambios a medias. |
| **Medida** | **Propuesta por validar:** el stock nunca queda negativo y siempre coincide con la suma de sus movimientos. |
| **Verificación** | Ejecutar una prueba de concurrencia contra la base de datos real. |
| **Estado** | Pendiente de implementar el módulo de inventario. |

## EQ-04. Rendimiento: consulta del panel de control

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Rendimiento (AC04) |
| **Fuente** | Almacenero o jefe de almacén |
| **Estímulo** | Abre el panel de control o registra una solicitud. |
| **Condición** | El sistema funciona normalmente con datos de prueba representativos. |
| **Respuesta esperada** | El sistema muestra la información sin errores. |
| **Medida** | **Propuesta por validar:** las operaciones responden en menos de 2 segundos. |
| **Verificación** | Medir los tiempos de respuesta con los datos de prueba. |
| **Estado** | Pendiente de definir el volumen de datos de prueba. |

## EQ-05. Usabilidad: registro de una solicitud

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Usabilidad (AC05) |
| **Fuente** | Almacenero |
| **Estímulo** | Registra una nueva solicitud desde su celular. |
| **Condición** | El usuario conoce los materiales que necesita. |
| **Respuesta esperada** | El usuario completa y envía la solicitud sin ayuda. |
| **Medida** | **Propuesta por validar:** el formulario tiene como máximo 5 campos y se completa en menos de 1 minuto. |
| **Verificación** | Revisar el formulario y cronometrar el registro con usuarios de prueba. |
| **Estado** | Pendiente de diseñar la interfaz. |

## EQ-06. Disponibilidad: falla de la aplicación

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Disponibilidad (AC06) |
| **Fuente** | Falla interna de la aplicación |
| **Estímulo** | El proceso de la aplicación se detiene inesperadamente. |
| **Condición** | El sistema está desplegado con Docker Compose. |
| **Respuesta esperada** | La aplicación se reinicia automáticamente y su estado se puede consultar. |
| **Medida** | **Propuesta por validar:** la aplicación vuelve a responder en menos de 1 minuto. |
| **Verificación** | Detener el contenedor manualmente y comprobar que se reinicia y responde. |
| **Estado** | Pendiente de configurar el despliegue. |

## EQ-07. Mantenibilidad: cambio en un módulo

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Mantenibilidad (AC07) |
| **Fuente** | Desarrolladora |
| **Estímulo** | Necesita modificar una regla de aprobación. |
| **Condición** | El sistema está organizado en módulos con capas. |
| **Respuesta esperada** | El cambio se realiza solo en el módulo de reglas, sin modificar los demás módulos. |
| **Medida** | **Propuesta por validar:** el cambio afecta a un solo módulo y las pruebas existentes siguen funcionando. |
| **Verificación** | Revisar los archivos modificados y ejecutar las pruebas. |
| **Estado** | Pendiente de implementar los módulos. |