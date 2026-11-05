# Escenarios de atributos de calidad del SGA

## EQ-01. Seguridad: acción no autorizada

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Seguridad |
| **Atributo relacionado (ID)** | AC01 |
| **Fuente** | Oficial de logística de una unidad |
| **Estímulo** | Intenta dar el visto bueno a un requerimiento o aprobar su atención en el almacén. |
| **Condición** | El usuario inició sesión correctamente. |
| **Respuesta esperada** | El sistema rechaza la acción porque no corresponde a su rol. Si el requerimiento pertenece a otra unidad, responde como si no existiera. |
| **Medida** | El 100 % de los intentos no autorizados es rechazado. |
| **Tipo de prueba** | Prueba de seguridad (control de acceso), ejecutada como prueba de integración de la API. |
| **Verificación** | Con **pytest** y **httpx**, un usuario de cada rol intenta firmar, aprobar o despachar un requerimiento que no le corresponde, y consultar uno de otra unidad. Se espera el rechazo de la API: sin sesión (401), sin permiso (403) o no encontrado (404). |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-02. Integridad: documento alterado

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Integridad |
| **Atributo relacionado (ID)** | AC02 |
| **Fuente** | Persona que modifica un documento firmado o un dato en la base de datos |
| **Estímulo** | Se cambia el contenido del PDF firmado o un dato del requerimiento ya firmado. |
| **Condición** | El requerimiento tiene al menos una firma registrada. |
| **Respuesta esperada** | Al verificar el documento, el sistema indica que fue **alterado**. |
| **Medida** | El 100 % de las alteraciones es detectado. |
| **Tipo de prueba** | Prueba unitaria (verificación de la firma) y prueba de integración (verificación con datos de la base de datos). |
| **Verificación** | Con **pytest** y la librería **cryptography**: la prueba unitaria cambia un byte del PDF firmado y comprueba que la firma Ed25519 ya no es válida; la prueba de integración cambia en la base de datos la cantidad de un ítem firmado y comprueba que la verificación responde **ALTERADO**. |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-03. Consistencia del inventario: despachos simultáneos

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Consistencia del inventario |
| **Atributo relacionado (ID)** | AC03 |
| **Fuente** | Dos almaceneros del mismo almacén |
| **Estímulo** | Despachan al mismo tiempo dos requerimientos cuyas cantidades juntas superan el stock disponible. |
| **Condición** | Ambos requerimientos están aprobados. |
| **Respuesta esperada** | Solo uno de los despachos se registra; el otro es rechazado sin dejar cambios a medias. |
| **Medida** | Diferencia de 0 unidades entre el stock y la suma de sus movimientos; el stock nunca queda negativo. |
| **Tipo de prueba** | Prueba de concurrencia, ejecutada como prueba de integración con la base de datos. |
| **Verificación** | Con **pytest**, dos hilos despachan al mismo tiempo 7 unidades cada uno de un ítem que tiene 10. Se comprueba que solo un despacho se registra y que el stock final es 3; luego, una consulta **SQL en PostgreSQL** confirma que ningún ítem tiene diferencia entre su stock y la suma de sus movimientos. |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-04. Rendimiento: operaciones habituales

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Rendimiento |
| **Atributo relacionado (ID)** | AC04 |
| **Fuente** | Usuarios de las unidades y de los almacenes |
| **Estímulo** | Registran, consultan y firman requerimientos al mismo tiempo. |
| **Condición** | El sistema funciona normalmente con datos de prueba ficticios. |
| **Respuesta esperada** | El sistema responde sin errores. |
| **Medida** | El 95 % de las operaciones responde en menos de 2 segundos con 20 usuarios simultáneos. |
| **Tipo de prueba** | Prueba de carga. |
| **Verificación** | Con **Locust** se simulan 20 usuarios durante 5 minutos: el 60 % consulta la lista de requerimientos, el 30 % consulta el detalle de uno y el 10 % registra uno nuevo. Locust reporta el percentil 95 del tiempo de respuesta y el porcentaje de errores de cada operación. |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-05. Usabilidad: registro desde un celular

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Usabilidad |
| **Atributo relacionado (ID)** | AC05 |
| **Fuente** | Oficial de logística de una unidad |
| **Estímulo** | Registra un nuevo requerimiento desde su celular. |
| **Condición** | El usuario conoce los materiales que necesita. |
| **Respuesta esperada** | El usuario completa y envía el requerimiento sin ayuda. |
| **Medida** | Máximo 5 campos en el formulario y puntaje de 80 o más en accesibilidad y buenas prácticas en modo celular. |
| **Tipo de prueba** | Prueba de usabilidad y accesibilidad. |
| **Verificación** | Con **Google Lighthouse** (Chrome DevTools, modo celular) se auditan tres pantallas: inicio de sesión, registro de requerimiento y bandeja de firmas. Cada una debe obtener 80 o más en accesibilidad y buenas prácticas; además, se cuentan los campos del formulario de registro. |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-06. Disponibilidad: falla de la aplicación

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Disponibilidad |
| **Atributo relacionado (ID)** | AC06 |
| **Fuente** | Falla interna de la aplicación |
| **Estímulo** | El contenedor de la aplicación se detiene inesperadamente. |
| **Condición** | El sistema está desplegado con Docker Compose, con reinicio automático y monitoreo activo. |
| **Respuesta esperada** | La aplicación se reinicia sola y vuelve a responder. |
| **Medida** | La aplicación vuelve a responder en menos de 1 minuto. |
| **Tipo de prueba** | Prueba de recuperación. |
| **Verificación** | Se fuerza la caída del contenedor de la API con el comando `docker kill`; **Docker Compose** lo reinicia automáticamente y **Uptime Kuma**, que revisa el punto `/health` cada 20 segundos, registra el tiempo de caída y de recuperación. La prueba se repite 3 veces. |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-07. Mantenibilidad: cambio de una regla

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Mantenibilidad |
| **Atributo relacionado (ID)** | AC07 |
| **Fuente** | Desarrolladora |
| **Estímulo** | Cambia el monto a partir del cual un requerimiento necesita la autorización del COLOGE. |
| **Condición** | El sistema está organizado en módulos con capas y tiene pruebas para cada módulo. |
| **Respuesta esperada** | El cambio se realiza solo en el módulo de Reglas y las demás pruebas siguen funcionando. |
| **Medida** | El cambio afecta a un solo módulo; cobertura de pruebas de 60 % o más en los módulos críticos y 0 errores de análisis de código. |
| **Tipo de prueba** | Prueba de regresión, medición de cobertura y análisis estático de código. |
| **Verificación** | Después del cambio: `git diff --stat` muestra que solo se modificaron archivos del módulo Reglas; la prueba de regresión con **pytest** ejecuta todas las pruebas y deben aprobarse; **pytest-cov** mide la cobertura; y **Ruff** analiza el código sin ejecutarlo. |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-08. Trazabilidad: recorrido del conducto regular

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Trazabilidad |
| **Atributo relacionado (ID)** | AC08 |
| **Fuente** | Auditor de la Inspectoría General |
| **Estímulo** | Consulta el historial de un requerimiento que recorrió todo el conducto regular. |
| **Condición** | El requerimiento fue firmado por todos los niveles y recibido por la unidad. |
| **Respuesta esperada** | El sistema muestra cada firma y movimiento con el usuario, su órgano y la fecha y hora. |
| **Medida** | El 100 % de las firmas y rechazos queda registrado con usuario, órgano y fecha. |
| **Tipo de prueba** | Prueba de extremo a extremo (E2E) a través de la API. |
| **Verificación** | Con **pytest** se recorre el flujo completo de un requerimiento de material de guerra: visto bueno, conformidad, autorización del COLOGE, aprobación, despacho y acta de recepción. Luego, una consulta **SQL en PostgreSQL** comprueba que los 6 pasos tienen usuario, órgano y fecha, y se ejecuta la verificación de la cadena de auditoría. |
| **Estado** | Pendiente de validar en el prototipo. |

## EQ-09. Escalabilidad: más usuarios con más instancias

| Elemento | Descripción |
|---|---|
| **Atributo de calidad** | Escalabilidad |
| **Atributo relacionado (ID)** | AC09 |
| **Fuente** | Incremento de usuarios de las unidades |
| **Estímulo** | La cantidad de usuarios simultáneos se duplica. |
| **Condición** | Se levanta una segunda instancia de la aplicación detrás del balanceador de carga. |
| **Respuesta esperada** | El sistema atiende a más usuarios sin cambiar su código. |
| **Medida** | Con 2 instancias se atiende a 40 usuarios simultáneos manteniendo el 95 % de las respuestas por debajo de 2 segundos. |
| **Tipo de prueba** | Prueba de escalabilidad (prueba de carga con escalamiento horizontal). |
| **Verificación** | Con **Locust** se simulan 40 usuarios dos veces: primero con 1 instancia de la API y luego con 2 instancias (`docker compose up --scale api=2`), con **Nginx** repartiendo las peticiones. Se comparan los percentiles 95 de ambas pruebas. |
| **Estado** | Pendiente de validar en el prototipo. |

## Resumen de escenarios

| Código | Atributo de calidad | Qué se busca comprobar | Tipo de prueba | Herramienta de software |
|---|---|---|---|---|
| EQ-01 | Seguridad | Que cada usuario solo pueda realizar las acciones de su rol y su órgano | Seguridad (control de acceso) | pytest + httpx |
| EQ-02 | Integridad | Que cualquier alteración de un documento firmado sea detectada | Unitaria e integración | pytest + cryptography |
| EQ-03 | Consistencia del inventario | Que el stock nunca quede inconsistente con operaciones simultáneas | Concurrencia | pytest + PostgreSQL |
| EQ-04 | Rendimiento | Que las operaciones respondan dentro del