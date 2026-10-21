# Restricciones

Identificar las **restricciones** que condicionan las decisiones de diseño y arquitectura del sistema.

| ID | Restricción | Descripción |
|---|---|---|
| RC01 | **Aplicación web responsiva** | El sistema debe desarrollarse como una aplicación accesible desde el navegador, tanto en computadora como en celular. |
| RC02 | **Control de versiones** | El código fuente y la documentación deben gestionarse con Git y mantenerse en un repositorio de GitHub. |
| RC03 | **API REST** | La comunicación entre el frontend y el backend debe realizarse mediante una API REST. |
| RC04 | **Desarrollo individual** | El sistema será construido por una sola persona, por lo que el alcance y la complejidad deben ser manejables. |
| RC05 | **Bajo costo** | Durante el desarrollo solo deben utilizarse herramientas gratuitas o de código abierto. |
| RC06 | **Firma electrónica del sistema** | La firma digital se realizará con una clave propia del sistema; no se utilizarán certificados digitales acreditados. |
| RC07 | **Despliegue con contenedores** | El sistema completo debe poder ejecutarse mediante Docker Compose. |