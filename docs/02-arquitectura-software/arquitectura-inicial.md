# Arquitectura inicial del sistema

## Diagrama de arquitectura

```mermaid
flowchart TD

%% =========================
%% ACTORES
%% =========================
subgraph ACTORES["ACTORES"]
    Almacenero["Almacenero"]
    Jefe["Jefe de almacén"]
    Admin["Administrador"]
end

%% =========================
%% PRESENTACIÓN
%% =========================
subgraph PRESENTACION["PRESENTACIÓN"]
    Web["Aplicación Web responsiva"]
    API["API REST"]
end

%% =========================
%% LÓGICA DE NEGOCIO
%% =========================
subgraph NEGOCIO["LÓGICA DE NEGOCIO"]
    Identidad["Identidad"]
    Catalogo["Catálogo"]
    Solicitudes["Solicitudes"]
    Reglas["Reglas"]
    Firma["Firma digital"]
    Inventario["Inventario"]
    Mensajeria["Mensajería"]
    Auditoria["Auditoría"]
    Reportes["Reportes"]
end

%% =========================
%% DATOS
%% =========================
subgraph DATOS["DATOS"]
    BD[("Base de datos")]
    Docs[("Documentos PDF firmados")]
end

%% =========================
%% FLUJO PRINCIPAL
%% =========================
ACTORES --> Web
Web --> API
API --> NEGOCIO
NEGOCIO --> BD
Firma --> Docs

%% =========================
%% DISTRIBUCIÓN HORIZONTAL
%% =========================
Almacenero ~~~ Jefe
Jefe ~~~ Admin

Identidad ~~~ Catalogo
Catalogo ~~~ Solicitudes
Solicitudes ~~~ Reglas
Reglas ~~~ Firma
Inventario ~~~ Mensajeria
Mensajeria ~~~ Auditoria
Auditoria ~~~ Reportes

%% =========================
%% ESTILOS
%% =========================
style ACTORES fill:#222,stroke:#fff,stroke-width:2px,color:#fff
style PRESENTACION fill:#222,stroke:#fff,stroke-width:2px,color:#fff
style NEGOCIO fill:#222,stroke:#fff,stroke-width:2px,color:#fff
style DATOS fill:#222,stroke:#fff,stroke-width:2px,color:#fff
```

## Descripción

| Capa | Elementos | Responsabilidad |
|---|---|---|
| **Actores** | Almacenero, jefe de almacén, administrador | Usan el sistema desde el navegador de una computadora o un celular. |
| **Presentación** | Aplicación web y API REST | Muestran las pantallas, reciben las peticiones y validan los datos de entrada. |
| **Lógica de negocio** | Nueve módulos | Aplican las reglas del negocio: aprobación, firma, inventario, alertas, prioridad y auditoría. |
| **Datos** | Base de datos y documentos firmados | Guardan la información del sistema y los PDF firmados, que no se modifican. |

> El proveedor externo solo se registra como origen de un pedido.