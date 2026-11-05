# Actores

Los actores son las personas que usan el sistema según su rol. Cada una pertenece a un órgano del Ejército del Perú (ver [Contexto organizacional](00-contexto-organizacional.md)).

| Actor | Órgano | ¿Qué necesita realizar? |
|---|---|---|
| **Oficial de logística de la unidad** | Unidad | Registrar los requerimientos de materiales de su unidad, registrar las salidas de su almacén, seguir el estado de cada requerimiento, revisar las alertas de stock y confirmar lo recibido firmando el acta de recepción. |
| **Comandante de la unidad** | Unidad | Dar el visto bueno con firma digital a los requerimientos de su unidad, o rechazarlos indicando el motivo. |
| **Jefe de logística de la Gran Unidad** | División de Ejército (I a V) o sus Brigadas | Revisar los requerimientos de las unidades de su jurisdicción y dar su conformidad con firma digital, o rechazarlos indicando el motivo. |
| **Jefe de Logística del COLOGE** | Comando Logístico del Ejército | Autorizar con firma digital los requerimientos de material de guerra o de montos altos. |
| **Jefe de almacén** | Servicio de Intendencia o Servicio de Material de Guerra | Aprobar o rechazar la atención de los requerimientos según el stock disponible, configurar los umbrales de stock y atender los requerimientos según su prioridad. |
| **Almacenero** | Servicio de Intendencia o Servicio de Material de Guerra | Preparar y despachar los materiales de los requerimientos aprobados, registrando las cantidades enviadas. |
| **Auditor** | Inspectoría General del Ejército | Consultar la trazabilidad de los requerimientos y verificar la integridad de los documentos firmados y de la auditoría. |
| **Administrador** | Dirección de Telemática y Estadística | Administrar órganos, unidades, almacenes, ítems, usuarios y reglas de aprobación, y registrar ajustes de inventario. |

> **Nota:** los órganos del Ejército no son actores; el sistema los registra como datos para saber a qué órgano pertenece cada usuario, unidad y almacén.
> La aprobación automática de los requerimientos de bajo riesgo tampoco es un actor: es una función interna del sistema, realizada por el módulo de Reglas.