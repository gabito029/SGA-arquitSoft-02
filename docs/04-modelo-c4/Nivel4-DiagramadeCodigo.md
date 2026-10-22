# Nivel 4 · Diagrama de código

> **Proyecto:** SGA · **Componentes detallados:** Solicitudes y Firma digital
> **Modelo:** C4 · Nivel 4 de 4 · **Versión:** 1.0

---

## 1. Objetivo

Mostrar las **clases principales** de los módulos Solicitudes y Firma digital, y cómo colaboran cuando se aprueba una solicitud.

| Aspecto | Descripción |
|---|---|
| Pregunta que responde | ¿Qué clases existen dentro de un módulo y cómo se relacionan? |
| Audiencia | Equipo de desarrollo |
| Notación | UML (diagrama de clases y diagrama de secuencia). El modelo C4 recomienda UML para este nivel |
| Por qué solo dos módulos | El nivel 4 es opcional en C4 y se dibuja solo para los componentes más importantes. Solicitudes y Firma digital concentran las reglas más críticas del sistema |
| Nivel anterior | `Nivel3-DiagramadeComponentes.md` |

---

## 2. Diagrama de clases

```mermaid
classDiagram
    class Request {
        +UUID id
        +str code
        +RequestType type
        +RequestStatus status
        +Priority priority
        +int version
    }
    class RequestItem {
        +UUID item_id
        +Decimal quantity
        +Decimal quantity_shipped
        +Decimal quantity_received
    }
    class RequestStatus {
        <<enumeration>>
        BORRADOR
        PENDIENTE_FIRMA
        APROBADA
        EN_TRANSITO
        CONFIRMADA
        RECHAZADA
        ANULADA
    }
    class RequestService {
        +submit(request_id, actor)
        +sign(request_id, actor, password)
        +dispatch(request_id, actor, items)
        +confirm_receipt(request_id, actor, items, note)
    }
    class RequestRepository {
        +get_for_update(request_id)
        +add(request)
    }
    class RulesService {
        +evaluate(request) Decision
    }
    class SigningService {
        +sign(request, purpose, signer) Signature
        +verify(request, purpose) str
    }
    class Signature {
        +str purpose
        +str document_hash
        +bytes signature
        +str pdf_sha256
    }
    class ObjectStorage {
        <<interface>>
        +put(key, data)
        +get(key) bytes
    }
    class LocalDiskStorage

    Request "1" *-- "1..*" RequestItem
    Request --> RequestStatus
    RequestService --> RequestRepository
    RequestService --> RulesService
    RequestService --> SigningService
    SigningService --> Signature
    SigningService --> ObjectStorage
    ObjectStorage <|.. LocalDiskStorage
```

### 2.1 Capas representadas

| Capa | Clases | Regla |
|---|---|---|
| **Modelos** | `Request`, `RequestItem`, `Signature` | Representan los datos guardados en la base de datos |
| **Servicio** | `RequestService`, `RulesService`, `SigningService` | Contienen las reglas del negocio |
| **Repositorio** | `RequestRepository` | Realiza las consultas a la base de datos |
| **Interfaz y adaptador** | `ObjectStorage`, `LocalDiskStorage` | El servicio de firma depende de la interfaz, no del disco |

---

## 3. Diagrama de secuencia: salida aprobada automáticamente

```mermaid
sequenceDiagram
    actor A as Almacenero
    participant API as API Solicitudes
    participant S as RequestService
    participant R as RulesService
    participant G as SigningService
    participant I as InventoryService
    participant AU as AuditService
    participant DB as PostgreSQL

    A->>API: Enviar solicitud
    API->>S: submit(id, actor)
    S->>DB: Iniciar transacción y bloquear la solicitud
    S->>S: Calcular monto y prioridad
    S->>R: evaluate(request)
    R-->>S: Aprobación automática
    S->>G: sign(request, APROBACION, SYSTEM)
    G-->>S: Firma y PDF guardado
    S->>I: Registrar salida y revisar alertas
    S->>AU: Registrar evento en la auditoría
    S->>DB: Confirmar transacción
    API-->>A: Solicitud APROBADA
```

> Si cualquier paso falla, la transacción se cancela y no se guarda ningún cambio.