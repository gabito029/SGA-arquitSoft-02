# Estilo arquitectónico

Se utiliza el estilo arquitectónico: **monolito modular + capas**.

| Elemento | Descripción aplicada al SGA |
|---|---|
| Estilo | Monolito modular: una sola aplicación desplegable, dividida en nueve módulos con responsabilidades claras. |
| ¿Por qué? | El sistema lo construye una sola persona; un único despliegue es más fácil de desarrollar, probar y ejecutar con Docker Compose. |
| Regla principal | Un módulo no accede directamente a los datos de otro; se comunica a través de los servicios que ese módulo ofrece. |
| Alternativa descartada | Microservicios: requieren varios despliegues, comunicación por red entre servicios y transacciones distribuidas, lo que dificultaría mantener consistente el inventario. |
| Evolución posible | Como cada módulo tiene límites claros, en el futuro podría separarse si el sistema crece. |

```mermaid
flowchart LR
    Navegador["Navegador"] --> App

    subgraph App["Aplicación única (monolito modular)"]
        direction TB
        M1["Identidad"] ~~~ M2["Catálogo"] ~~~ M3["Solicitudes"]
        M4["Reglas"] ~~~ M5["Firma digital"] ~~~ M6["Inventario"]
        M7["Mensajería"] ~~~ M8["Auditoría"] ~~~ M9["Reportes"]
    end

    App --> BD[("Base de datos")]
```