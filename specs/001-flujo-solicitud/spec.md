# Feature Specification: Flujo principal de abastecimiento (solicitud → acta de recepción firmada)

**Feature Branch**: `001-flujo-solicitud`

**Created**: 2026-11-22

**Status**: Draft

**Input**: User description: "Especificar el incremento 001 del SGA: el flujo principal de
abastecimiento de punta a punta para intendencia y material de guerra. El oficial de logística
registra una solicitud, la División/Brigada de su unidad la aprueba o rechaza, el almacén la
despacha sin superar el stock y el oficial de logística firma digitalmente el acta de recepción,
que queda inmutable y verificable. Estados sin saltos, historial de cada cambio, nada se elimina,
anulación solo con justificación y visibilidad por rol y unidad/División."

## Fuente de verdad y conflictos con el pedido

Según la constitución (principio I), `docs/` prevalece sobre el pedido; los conflictos se
reportan aquí y no se resuelven en silencio. Este incremento implementa HU01, HU02, HU03, HU05,
HU07 y HU08 (RF01, RF02, RF03, RF05, RF06, RF07, RF08) de `docs/`.

| # | Pedido original | Lo que fija `docs/` | Cómo queda en esta especificación |
|---|---|---|---|
| C1 | La solicitud pasa directamente a la División/Brigada | El conducto regular empieza con el **visto bueno del comandante de la unidad** (HU03, diagrama de estados) y ningún nivel puede omitirse (RN02) | Se incluye el visto bueno del comandante de la unidad antes de la División/Brigada |
| C2 | El jefe de almacén despacha | El **jefe de almacén aprueba** la atención según el stock (HU05) y el **almacenero despacha** (HU07) | Se incluyen ambos pasos, con sus dos roles |
| C3 | Solo se firma el acta de recepción | **Cada paso del conducto regular** se firma digitalmente (RF05, ADR-004), además del acta | Cada aprobación es una firma digital; el acta también |
| C4 | Estados: Registrada → Aprobada/Rechazada → Despachada → Recibida | Estados del diagrama de `docs/`: BORRADOR, PENDIENTE_VB_UNIDAD, PENDIENTE_CONFORMIDAD, PENDIENTE_AUTORIZACION_COLOGE, PENDIENTE_APROBACION, APROBADA, RECHAZADA, ANULADA, EN_TRANSITO, CONFIRMADA | Se usan los estados de `docs/` con los nombres del pedido como etiquetas (ver tabla de estados) |
| C5 | Anular en cualquier momento antes del despacho | El diagrama solo permite anular desde BORRADOR; RN06 dice que, una vez despachada, ya no puede anularse | Solo se anula desde "Registrada", literal al diagrama; es más estricto que RN06 y no lo contradice (FR-022) |
| C6 | Intendencia y material de guerra | El material de guerra y los montos altos requieren **autorización del COLOGE** (RN03, HU04); la constitución pospone ese nivel | Se puede registrar, pero el envío de las solicitudes que requieren al COLOGE se bloquea con un aviso hasta el incremento 002 (FR-012); no se salta ningún nivel |
| C7 | — | Los requerimientos de bajo riesgo se aprueban automáticamente en el almacén (RN04, HU06) | Pospuesto: en este incremento todas las solicitudes pasan por la aprobación manual del jefe de almacén (desviación temporal declarada en la constitución) |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar y enviar una solicitud de material (Priority: P1)

El oficial de logística de una unidad inicia sesión, registra una solicitud con uno o más ítems
del catálogo (intendencia o material de guerra) y sus cantidades, y la envía por el conducto
regular. Desde ese momento puede seguir su estado en una línea de tiempo.

**Why this priority**: sin solicitud no hay flujo; reemplaza el oficio en papel y es el punto de
entrada de todo el incremento.

**Independent Test**: con usuarios de prueba, el oficial registra y envía una solicitud y la ve en
su lista con estado "En visto bueno de la unidad" y su primera entrada en el historial.

**Acceptance Scenarios**:

1. **Dado** un oficial de logística autenticado de la unidad U1, **Cuando** registra una solicitud
   con 2 ítems de intendencia y cantidades positivas y la envía, **Entonces** la solicitud queda en
   estado "En visto bueno de la unidad", asociada a U1, y el historial registra el usuario, la
   fecha y hora, el estado anterior (Registrada) y el nuevo.
2. **Dado** un oficial que registra una solicitud, **Cuando** la guarda sin enviarla, **Entonces**
   queda en estado "Registrada" y solo la ven los oficiales de logística de su unidad.
3. **Dado** un formulario de solicitud, **Cuando** el oficial intenta enviarla sin ítems, con
   cantidad cero o negativa, o con un ítem repetido, **Entonces** el envío se rechaza con un
   mensaje que indica el campo y el motivo.
4. **Dado** un usuario con otro rol (por ejemplo, almacenero), **Cuando** intenta registrar una
   solicitud, **Entonces** la acción se rechaza por falta de permiso.
5. **Dado** un oficial que registra una solicitud de material de guerra, **Cuando** la guarda,
   **Entonces** queda en "Registrada"; **Cuando** intenta enviarla, **Entonces** el envío se
   bloquea con el aviso "Requiere autorización del COLOGE (disponible en un próximo incremento)",
   la solicitud sigue en "Registrada" y el intento bloqueado queda en el historial.
6. **Dada** una solicitud de intendencia cuyo monto total alcanza el umbral de monto alto,
   **Cuando** el oficial intenta enviarla, **Entonces** el envío se bloquea con el mismo aviso.

---

### User Story 2 - Aprobar o rechazar por el conducto regular (Priority: P1)

El comandante de la unidad da su visto bueno y, después, el jefe de logística de la División o
Brigada a la que pertenece la unidad da su conformidad. Cada uno firma digitalmente su decisión o
rechaza indicando el motivo. Ningún nivel se puede saltar y nadie de otra jurisdicción puede
actuar.

**Why this priority**: el conducto regular es la regla institucional central (RC09); sin él la
solicitud no puede llegar al almacén.

**Independent Test**: con una solicitud enviada, el comandante de U1 da el visto bueno y el jefe de
logística de la División de U1 da su conformidad; se comprueba que un comandante de otra unidad y
un jefe de logística de otra División no pueden actuar.

**Acceptance Scenarios**:

1. **Dada** una solicitud de U1 en "En visto bueno de la unidad", **Cuando** el comandante de U1
   la firma, **Entonces** pasa a "En conformidad de la División/Brigada" y el historial registra la
   firma con usuario, órgano, fecha y hora.
2. **Dada** una solicitud de U1 en "En conformidad de la División/Brigada", **Cuando** el jefe de
   logística de la División/Brigada de U1 la firma, **Entonces** pasa a "En aprobación del almacén".
3. **Dada** una solicitud de U1 en "En visto bueno de la unidad", **Cuando** el jefe de logística
   de la División intenta dar su conformidad antes del visto bueno, **Entonces** la acción se
   rechaza porque no corresponde al estado actual y la solicitud no cambia.
4. **Dada** una solicitud de U1, **Cuando** un jefe de logística de otra División intenta verla o
   firmarla, **Entonces** el sistema responde como si la solicitud no existiera.
5. **Dada** una solicitud pendiente de su nivel, **Cuando** el firmante la rechaza sin motivo,
   **Entonces** el rechazo no se registra y se le pide el motivo; **Cuando** la rechaza con motivo,
   **Entonces** pasa a "Rechazada", el motivo queda en el historial y ningún otro nivel puede
   actuar sobre ella.
6. **Dada** una solicitud que un nivel ya firmó, **Cuando** el mismo usuario intenta firmarla de
   nuevo, **Entonces** la acción se rechaza (cada nivel firma una sola vez).

---

### User Story 3 - Aprobar la atención y despachar sin superar el stock (Priority: P1)

El jefe de almacén consulta las solicitudes que llegan a su almacén, aprueba con firma digital las
que puede atender según el stock o las rechaza con motivo. El almacenero despacha las aprobadas
indicando las cantidades enviadas, y el stock se descuenta en ese momento.

**Why this priority**: sin despacho no hay recepción; es donde se protege la consistencia del
inventario (AC03).

**Independent Test**: con una solicitud en "En aprobación del almacén" y stock suficiente, el jefe
de almacén aprueba, el almacenero despacha y el stock baja exactamente en las cantidades enviadas.

**Acceptance Scenarios**:

1. **Dada** una solicitud en "En aprobación del almacén" con stock suficiente, **Cuando** el jefe
   de almacén la aprueba con firma, **Entonces** pasa a "Aprobada".
2. **Dada** una solicitud en "En aprobación del almacén", **Cuando** el jefe de almacén la rechaza
   con motivo (por ejemplo, stock insuficiente), **Entonces** pasa a "Rechazada" con el motivo en
   el historial.
3. **Dada** una solicitud "Aprobada" de 7 unidades de un ítem con stock 10, **Cuando** el
   almacenero la despacha, **Entonces** pasa a "Despachada", se registra un movimiento de salida de
   7 unidades y el stock queda en 3.
4. **Dada** una solicitud "Aprobada" de un ítem cuyo stock actual es menor que la cantidad a
   despachar, **Cuando** el almacenero intenta despacharla, **Entonces** el despacho se rechaza, no
   se registra ningún movimiento y el stock no cambia.
5. **Dadas** dos solicitudes "Aprobadas" de 7 unidades cada una de un ítem con stock 10,
   **Cuando** dos almaceneros las despachan al mismo tiempo, **Entonces** solo un despacho se
   registra, el otro se rechaza sin cambios a medias y el stock final es 3.
6. **Dada** una solicitud que no está "Aprobada", **Cuando** el almacenero intenta despacharla,
   **Entonces** la acción se rechaza.

---

### User Story 4 - Firmar el acta de recepción y verificar su integridad (Priority: P1)

Cuando el material llega, el oficial de logística de la unidad solicitante confirma lo recibido
(registrando diferencias si las hay) y firma digitalmente el acta de recepción. El acta queda
inmutable y cualquier usuario autorizado puede verificar que no fue alterada.

**Why this priority**: cierra el flujo y reemplaza el acta en papel, que podía alterarse o
perderse.

**Independent Test**: con una solicitud "Despachada", el oficial firma el acta; la verificación
responde "Íntegra"; si se altera un dato firmado, la verificación responde "Alterada".

**Acceptance Scenarios**:

1. **Dada** una solicitud de U1 "Despachada", **Cuando** el oficial de logística de U1 registra las
   cantidades recibidas y firma el acta, **Entonces** la solicitud pasa a "Recibida" y el acta
   guarda quién firmó, cuándo y las diferencias entre lo despachado y lo recibido.
2. **Dada** una solicitud "Despachada" de U1, **Cuando** un oficial de logística de otra unidad, o
   un usuario de otro rol, intenta firmar el acta, **Entonces** la acción se rechaza.
3. **Dada** un acta firmada, **Cuando** cualquier usuario intenta modificarla o firmarla otra vez,
   **Entonces** la acción se rechaza y el acta no cambia.
4. **Dada** un acta firmada sin cambios, **Cuando** un usuario autorizado solicita su
   verificación, **Entonces** el resultado es "Íntegra", con el firmante y la fecha de firma.
5. **Dada** un acta firmada cuyos datos firmados se alteraron fuera del sistema, **Cuando** se
   verifica, **Entonces** el resultado es "Alterada".
6. **Dada** una solicitud que no está "Despachada", **Cuando** el oficial intenta firmar el acta,
   **Entonces** la acción se rechaza.

---

### User Story 5 - Seguir la línea de tiempo de una solicitud (Priority: P2)

Cada usuario consulta las solicitudes que le corresponden y, en cada una, su línea de tiempo:
cada cambio de estado, firma y rechazo con quién, en qué órgano, cuándo y desde qué estado.

**Why this priority**: da la trazabilidad que el papel no ofrece (AC08); el flujo ya funciona sin
ella, pero sin ella no se puede auditar.

**Independent Test**: después de recorrer el flujo completo, la línea de tiempo muestra todos los
pasos en orden con usuario, órgano, fecha y hora y estado anterior.

**Acceptance Scenarios**:

1. **Dada** una solicitud "Recibida", **Cuando** el oficial de logística de su unidad abre su
   línea de tiempo, **Entonces** ve, en orden, el envío, el visto bueno, la conformidad, la
   aprobación del almacén, el despacho y el acta, cada uno con usuario, órgano, fecha y hora y
   estado anterior.
2. **Dado** un usuario de cualquier rol, **Cuando** abre su bandeja, **Entonces** solo ve las
   solicitudes de su unidad, de su jurisdicción o de su almacén, según su rol, de forma paginada.
3. **Dado** cualquier usuario, **Cuando** intenta borrar o editar una entrada del historial,
   **Entonces** no existe forma de hacerlo.

---

### User Story 6 - Anular una solicitud con justificación (Priority: P3)

El oficial de logística de la unidad anula una solicitud que aún no envió, indicando el motivo.
La solicitud no se borra: queda en estado "Anulada" con su historial completo. Una vez enviada, la
única salida antes del despacho es que un firmante la rechace.

**Why this priority**: es necesaria para descartar solicitudes sin borrarlas (por ejemplo, las de
material de guerra bloqueadas hasta el COLOGE), pero el flujo principal funciona sin ella.

**Independent Test**: el oficial anula con motivo una solicitud en "Registrada"; queda "Anulada" y
visible en su lista y en su historial.

**Acceptance Scenarios**:

1. **Dada** una solicitud de U1 en "Registrada", **Cuando** el oficial de logística de U1 la anula
   con motivo, **Entonces** pasa a "Anulada" y el motivo queda en el historial.
2. **Dada** una solicitud en "Registrada", **Cuando** se intenta anular sin motivo, **Entonces** la
   anulación se rechaza.
3. **Dada** una solicitud en cualquier estado distinto de "Registrada" (en firmas, Aprobada,
   Despachada, Recibida, Rechazada), **Cuando** se intenta anular, **Entonces** la anulación se
   rechaza y la solicitud no cambia.
4. **Dada** una solicitud de U1 en "Registrada", **Cuando** un usuario de otra unidad o de otro rol
   intenta anularla, **Entonces** la acción se rechaza.

---

### Edge Cases

- **Solicitud que requiere al COLOGE**: material de guerra o monto alto; se puede guardar y
  anular, pero nunca enviar en este incremento, y por lo tanto nunca llega a ningún firmante.
- **Saltos de nivel**: cualquier intento de pasar a un estado que no sigue al actual (por ejemplo,
  despachar una solicitud en conformidad) se rechaza y la solicitud no cambia.
- **Doble acción simultánea**: si dos usuarios del mismo nivel intentan firmar o rechazar la misma
  solicitud a la vez, solo una acción se registra; la otra recibe un aviso de que la solicitud ya
  cambió de estado.
- **Stock cambia entre la aprobación y el despacho**: la aprobación del jefe de almacén no reserva
  stock; si al despachar el stock ya no alcanza, el despacho se rechaza y la solicitud sigue
  "Aprobada".
- **Despacho parcial**: el almacenero puede enviar menos de lo aprobado, nunca más; la diferencia
  queda registrada en el despacho y en el acta.
- **Recepción con diferencias**: si llega menos (o algo dañado), el oficial registra la cantidad
  recibida y una observación; el acta se firma igual y las diferencias quedan firmadas en ella.
- **Usuario sin unidad o sin jurisdicción en los datos de prueba**: no puede operar ninguna
  solicitud.
- **Ítem desactivado en el catálogo**: no puede agregarse a una nueva solicitud; las solicitudes
  existentes que lo contienen siguen su curso.
- **Solicitud de otra unidad**: consultarla o actuar sobre ella responde como si no existiera.
- **Sesión expirada** durante una acción: la acción no se ejecuta y se pide iniciar sesión de
  nuevo.
- **Acta firmada y verificación con datos alterados** en cualquier campo firmado (ítems,
  cantidades, firmante, fecha): siempre responde "Alterada".

## Requirements *(mandatory)*

### Estados de la solicitud

| Etiqueta en la interfaz | Estado en `docs/` | Quién actúa para salir de él |
|---|---|---|
| Registrada | BORRADOR | Oficial de logística (enviar o anular) |
| En visto bueno de la unidad | PENDIENTE_VB_UNIDAD | Comandante de la unidad |
| En conformidad de la División/Brigada | PENDIENTE_CONFORMIDAD | Jefe de logística de la División/Brigada |
| En autorización del COLOGE | PENDIENTE_AUTORIZACION_COLOGE | Jefe de Logística del COLOGE (incremento 002; no se alcanza en el 001, ver FR-012) |
| En aprobación del almacén | PENDIENTE_APROBACION | Jefe de almacén |
| Aprobada | APROBADA | Almacenero (despachar) |
| Despachada | EN_TRANSITO | Oficial de logística (firmar el acta) |
| Recibida | CONFIRMADA | Estado final |
| Rechazada | RECHAZADA | Estado final |
| Anulada | ANULADA | Estado final |

### Functional Requirements

**Acceso y visibilidad**

- **FR-001**: El sistema DEBE exigir inicio de sesión para toda funcionalidad, salvo la propia
  pantalla de inicio de sesión.
- **FR-002**: El sistema DEBE permitir a cada usuario ver y operar solo lo que corresponde a su
  rol y órgano: el oficial de logística y el comandante, las solicitudes de su unidad; el jefe de
  logística de la División/Brigada, las de las unidades de su jurisdicción; el jefe de almacén y
  el almacenero, las dirigidas a su almacén desde que llegan a "En aprobación del almacén". Una
  solicitud en "Registrada" solo la ven los oficiales de logística de su unidad; ningún otro rol,
  ni siquiera el comandante o el auditor, la ve antes del envío.
- **FR-003**: Ante una acción sin sesión, sin permiso o sobre una solicitud ajena, el sistema DEBE
  rechazarla distinguiendo los tres casos; una solicitud de otra unidad o jurisdicción DEBE
  tratarse como inexistente.
- **FR-004**: Los usuarios, roles, órganos (unidades, Divisiones/Brigadas, almacenes), el catálogo
  de ítems y el stock inicial DEBEN cargarse como datos de prueba ficticios; no hay pantallas para
  administrarlos en este incremento.

**Registro de la solicitud**

- **FR-005**: El oficial de logística DEBE poder registrar una solicitud con uno o más ítems del
  catálogo activo y una cantidad entera positiva por ítem, con un formulario de **5 campos como
  máximo** por pantalla.
- **FR-006**: El sistema DEBE asociar cada solicitud a la unidad del oficial que la registra y al
  almacén del servicio que corresponde a la categoría de sus ítems.
- **FR-007**: Una solicitud DEBE contener ítems de una sola categoría (intendencia o material de
  guerra), para que se dirija a un único almacén.
- **FR-008**: El oficial DEBE poder guardar la solicitud en "Registrada" y editarla mientras siga
  en ese estado; al enviarla deja de ser editable.

**Conducto regular**

- **FR-009**: El sistema DEBE aplicar exclusivamente las transiciones de la tabla de estados en
  el orden de `docs/`; cualquier otra transición DEBE rechazarse sin cambiar la solicitud.
- **FR-010**: Solo el comandante de la unidad solicitante DEBE poder dar el visto bueno, y solo el
  jefe de logística de la División/Brigada a la que pertenece esa unidad DEBE poder dar la
  conformidad.
- **FR-011**: Solo el jefe de almacén del almacén destino DEBE poder aprobar la atención.
- **FR-012**: El sistema DEBE aplicar la regla RN03 al enviar: si la solicitud es de material de
  guerra o su monto total alcanza el umbral de monto alto definido en la configuración (ADR-008),
  requiere autorización del COLOGE. Como ese nivel llega en el incremento 002, el envío DEBE
  bloquearse con el aviso "Requiere autorización del COLOGE (disponible en un próximo
  incremento)"; la solicitud sigue en "Registrada" y el intento queda en el historial. Ningún
  nivel se omite.
- **FR-013**: Cada nivel DEBE actuar una sola vez por solicitud.
- **FR-014**: Cualquier firmante DEBE poder rechazar la solicitud en su nivel, con motivo
  obligatorio; una solicitud rechazada no admite más acciones.
- **FR-015**: Cada aprobación (visto bueno, conformidad, aprobación del almacén) DEBE registrarse
  como una firma digital ligada al firmante, su rol, su órgano, la fecha y hora y el contenido de
  la solicitud en ese momento.
- **FR-016**: Si dos usuarios actúan a la vez sobre la misma solicitud, solo la primera acción
  válida DEBE registrarse; la otra DEBE recibir un aviso de que la solicitud cambió.

**Despacho e inventario**

- **FR-017**: El almacenero del almacén destino DEBE poder despachar una solicitud "Aprobada",
  indicando la cantidad enviada de cada ítem, igual o menor que la aprobada.
- **FR-018**: El sistema NO DEBE permitir despachar una cantidad mayor que el stock disponible en
  el momento del despacho; el stock nunca DEBE quedar negativo.
- **FR-019**: El despacho DEBE registrar un movimiento de salida por ítem y descontar el stock en
  una sola operación indivisible junto con el cambio de estado y su historial: o se guarda todo o
  no se guarda nada.
- **FR-020**: El stock de cada ítem DEBE coincidir en todo momento con la suma de sus
  movimientos; los movimientos no pueden modificarse ni borrarse.

**Acta de recepción**

- **FR-021**: Solo el oficial de logística de la unidad solicitante DEBE poder firmar el acta de
  recepción de una solicitud "Despachada", registrando la cantidad recibida por ítem y
  observaciones de las diferencias; al firmarla la solicitud pasa a "Recibida".
- **FR-022**: El oficial de logística de la unidad DEBE poder anular su solicitud, con motivo
  obligatorio, **solo mientras esté en "Registrada"** (transición BORRADOR → ANULADA del diagrama
  de `docs/`). En cualquier otro estado la anulación DEBE rechazarse.
- **FR-023**: El acta firmada DEBE ser inmutable: ninguna operación del sistema puede modificarla
  ni volver a firmarla.
- **FR-024**: El sistema DEBE permitir a los usuarios que pueden ver la solicitud, y al auditor
  cargado en los datos de prueba, verificar la integridad del acta y de cada firma del conducto
  regular, con resultado "Íntegra" o "Alterada", el firmante y la fecha de firma.
- **FR-025**: La verificación DEBE detectar cualquier alteración de los datos firmados, incluida
  la modificación directa en el almacenamiento.

**Trazabilidad**

- **FR-026**: Cada cambio de estado, firma, rechazo, anulación y despacho DEBE registrar el
  usuario, su rol, su órgano, la fecha y hora, el estado anterior, el estado nuevo y el motivo
  cuando aplique.
- **FR-027**: Ningún registro de negocio (solicitud, firma, movimiento, acta, historial) DEBE
  poder eliminarse; las correcciones se hacen con nuevos registros.
- **FR-028**: El sistema DEBE mostrar la línea de tiempo de cada solicitud con todas sus firmas y
  cambios de estado en orden cronológico.
- **FR-029**: Los listados de solicitudes DEBEN estar paginados y poder filtrarse por estado.

**Interfaz**

- **FR-030**: La interfaz DEBE poder usarse desde una computadora y desde un celular, mostrar a
  cada rol solo sus opciones, validar los formularios antes de enviarlos, mostrar mensajes de
  error comprensibles en español e indicar cuándo una acción está en curso.

### Key Entities *(include if feature involves data)*

- **Órgano**: unidad, División/Brigada (Gran Unidad), COLOGE o servicio con su almacén; tiene un
  órgano padre que define la jurisdicción (cada unidad pertenece a una División/Brigada).
- **Usuario**: persona con un rol (oficial de logística, comandante de la unidad, jefe de
  logística de la Gran Unidad, jefe de almacén, almacenero, auditor) y un órgano.
- **Almacén**: pertenece a un servicio (Intendencia o Material de Guerra) y guarda el stock de los
  ítems de su categoría.
- **Ítem**: material del catálogo con categoría (intendencia o material de guerra), unidad de
  medida, valor unitario referencial (para calcular el monto de la solicitud) y estado
  activo/inactivo.
- **Stock**: cantidad disponible de un ítem en un almacén; es la suma de sus movimientos.
- **Movimiento**: entrada o salida de un ítem en un almacén, con cantidad, usuario, fecha y la
  solicitud que la originó; no se modifica.
- **Solicitud (requerimiento)**: unidad solicitante, almacén destino, categoría, estado actual e
  ítems con cantidad solicitada, despachada y recibida. Equivale a la PECOSA (RC11).
- **Firma**: decisión firmada de un nivel (visto bueno, conformidad, aprobación o acta), con
  firmante, rol, órgano, fecha y hora, huella del contenido firmado y firma digital.
- **Acta de recepción**: documento firmado por el oficial de logística con lo recibido y las
  diferencias; inmutable y verificable.
- **Entrada de historial**: cambio de estado con usuario, rol, órgano, fecha y hora, estado
  anterior, estado nuevo y motivo; no se modifica ni se elimina.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (Seguridad, EQ-01): el 100 % de los intentos de firmar, aprobar, despachar o firmar el
  acta por un usuario sin el rol u órgano correspondiente es rechazado, y el 100 % de las consultas
  a solicitudes de otra unidad responde como inexistente.
- **SC-002** (Integridad, EQ-02): el 100 % de las alteraciones de un acta o de una firma es
  detectado al verificarla.
- **SC-003** (Consistencia del inventario, EQ-03): con despachos simultáneos que juntos superan el
  stock, solo uno se registra, el stock nunca queda negativo y la diferencia entre el stock y la
  suma de sus movimientos es de 0 unidades.
- **SC-004** (Rendimiento, EQ-04): con 20 usuarios simultáneos que consultan, abren y registran
  solicitudes durante 5 minutos, el 95 % de las operaciones responde en menos de 2 segundos y sin
  errores.
- **SC-005** (Usabilidad, EQ-05): un oficial de logística registra y envía una solicitud desde un
  celular sin ayuda, con 5 campos como máximo, y las pantallas de inicio de sesión, registro y
  bandeja obtienen 80 o más en las auditorías de accesibilidad y buenas prácticas en modo celular.
  *Se valida en el incremento 002 (Lighthouse); en 001 el formulario ya respeta los 5 campos.*
- **SC-006** (Trazabilidad, EQ-08): después de recorrer el flujo completo, el 100 % de los pasos
  (envío, visto bueno, conformidad, aprobación, despacho y acta) aparece en la línea de tiempo con
  usuario, órgano, fecha y hora y estado anterior.
- **SC-007** (Escalabilidad, EQ-09): al duplicar los usuarios simultáneos a 40 y duplicar las
  instancias de la aplicación, el 95 % de las respuestas sigue por debajo de 2 segundos.
  *Se valida en el incremento 002 (k6); en 001 solo se escribe el script.*
- **SC-008** (Disponibilidad, EQ-06): si la aplicación se detiene inesperadamente, vuelve a
  responder sola en menos de 1 minuto. *Se valida en el incremento 002 (`docker kill` y Uptime
  Kuma); en 001 ya están `restart: always` y `/health`.*
- **SC-009** (Flujo completo): una solicitud recorre el flujo completo, del registro al acta
  firmada, en menos de 10 minutos de trabajo acumulado de todos los participantes, frente a los
  días que toma hoy con oficios en papel.

## Assumptions

- Los usuarios, órganos, almacenes, ítems y stock inicial son ficticios y se cargan como datos de
  prueba (RC13); habrá al menos 2 Divisiones/Brigadas, 2 unidades por cada una y un almacén por
  servicio, para poder probar el aislamiento entre jurisdicciones.
- "Comandante/encargado de la División o Brigada" del pedido corresponde al rol **Jefe de
  logística de la Gran Unidad** de `docs/01-analisis-de-sistema/01-actores.md`.
- La firma digital usa la clave del sistema según ADR-004 y no tiene validez legal plena (RC01);
  en este incremento la firma de cada nivel y del acta se verifica con el endpoint de verificación
  (Íntegra o Alterada), y el PDF verificable de cada firma y del acta (RF05) se implementa
  obligatoriamente en el incremento 002 (desviación temporal DT-01 de la constitución v1.2.0).
- En este incremento el entorno local usa HTTP; HTTPS (AC01) se implementa en el incremento 002
  junto con el despliegue (desviación temporal DT-02 de la constitución v1.2.0).
- La aprobación del jefe de almacén no reserva stock; el stock se valida y descuenta solo al
  despachar.
- El auditor existe solo como usuario de prueba con acceso de consulta y verificación; las
  funciones propias del auditor (HU12: verificación de la auditoría encadenada) llegan después.
- La aprobación automática de bajo riesgo (RN04, HU06) se pospone: todas las solicitudes pasan por
  la aprobación del jefe de almacén.
- El nivel del COLOGE (HU04) es el **incremento 002**. Hasta entonces, el flujo completo solo se
  recorre con solicitudes de intendencia por debajo del umbral de monto alto. Los ítems de prueba
  tienen un valor unitario referencial, y el umbral es un valor de configuración ficticio.
- Fuera de alcance: gestión de usuarios y catálogo (HU11), registro de salidas propias de la unidad
  (HU09), alertas de stock (HU10), panel y reportes (HU13), notificaciones, mensajería, compras a
  proveedores, presupuesto y el SIGA MEF.
