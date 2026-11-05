# Restricciones

Identificar las **restricciones** que condicionan las decisiones de diseño y arquitectura del sistema.

| ID | Restricción | Descripción | Origen |
|---|---|---|---|
| RC01 | **Firma electrónica del sistema** | Según la Ley N° 27269, Ley de Firmas y Certificados Digitales, una firma digital equivale a la firma manuscrita solo si usa un certificado de una entidad acreditada en la Infraestructura Oficial de Firma Electrónica (IOFE). El prototipo usa una clave propia del sistema, que garantiza la integridad de los documentos, pero no tiene validez legal plena; el uso de certificados acreditados queda como evolución. | Normativa |
| RC02 | **Aplicación web responsiva** | El sistema debe desarrollarse como una aplicación accesible desde el navegador, tanto en computadora como en celular. | Contexto |
| RC03 | **Spec-Driven Development (SDD)** | El desarrollo debe seguir la metodología SDD: primero se redactan las especificaciones de cada módulo y luego se genera el código a partir de ellas con apoyo de inteligencia artificial (Claude Code). | Docente |
| RC04 | **Control de versiones** | El código fuente y la documentación deben gestionarse con Git y mantenerse en un repositorio de GitHub. | Docente |
| RC05 | **API REST** | La comunicación entre el frontend y el backend debe realizarse mediante una API REST. | Propuesta |
| RC06 | **Desarrollo individual** | El sistema será construido por una sola persona, por lo que el alcance y la complejidad deben ser manejables. | Contexto |
| RC07 | **Bajo costo** | Durante el desarrollo solo deben utilizarse herramientas gratuitas o de código abierto. | Contexto |
| RC08 | **Despliegue con contenedores** | El sistema completo debe poder ejecutarse mediante Docker Compose. | Propuesta |
| RC09 | **Conducto regular** | Todo requerimiento debe seguir los niveles jerárquicos del Ejército: unidad, gran unidad, COLOGE cuando corresponda y almacén. | Contexto |
| RC10 | **Estructura orgánica del Ejército** | El sistema debe respetar la organización del Ejército del Perú: cada usuario, unidad y almacén pertenece a un órgano. | Contexto |
| RC11 | **Sistema Nacional de Abastecimiento** | El almacenamiento y la distribución de bienes en el sector público se rigen por el Decreto Legislativo N° 1439 y la Directiva N° 0004-2021-EF/54.01, que permiten documentos físicos o electrónicos. El requerimiento del SGA equivale al Pedido Comprobante de Salida (PECOSA). | Normativa |
| RC12 | **Sin integración con el SIGA MEF** | El Sistema Integrado de Gestión Administrativa (SIGA MEF) es el sistema oficial del Estado para la gestión de bienes; el prototipo funciona de forma independiente y no se integra con él. | Contexto |
| RC13 | **Datos de prueba ficticios** | La información logística del Ejército es sensible; las pruebas y la demostración se realizan con datos ficticios pero realistas. | Contexto |