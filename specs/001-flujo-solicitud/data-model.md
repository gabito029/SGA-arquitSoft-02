# Data Model: Incremento 001 — Flujo principal de abastecimiento

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md)

Nombres de tablas y columnas en español sin tildes (diseño interno de `docs/`). Todas las fechas
son `timestamptz` en UTC. Las tablas marcadas **(inmutable)** tienen un disparador que rechaza
`UPDATE` y `DELETE` (research §6).

## 1. Catálogo (módulo `catalog`)

### organo
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| codigo | text único | p. ej. `1DE`, `BIM-11` |
| nombre | text | |
| tipo | enum `TipoOrgano` | `UNIDAD`, `GRAN_UNIDAD`, `COLOGE`, `SERVICIO` |
| padre_id | uuid FK → organo, nulo | una `UNIDAD` DEBE tener padre `GRAN_UNIDAD` (ADR-009) |

### almacen
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| nombre | text | |
| organo_id | uuid FK → organo (`SERVICIO`) | |
| categoria | enum `Categoria` | `INTENDENCIA`, `MATERIAL_GUERRA`; un almacén por categoría en los seeds |

### item
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| codigo | text único | |
| nombre | text | |
| categoria | enum `Categoria` | |
| unidad_medida | text | p. ej. `unidad`, `caja`, `kg` |
| valor_unitario | numeric(12,2) | ≥ 0; referencial para el monto alto (FR-012) |
| activo | bool | un ítem inactivo no puede agregarse a solicitudes nuevas |

## 2. Identidad (módulo `identity`)

### usuario
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| usuario | text único | nombre de inicio de sesión |
| nombre_completo | text | |
| hash_contrasena | text | bcrypt; nunca se expone |
| rol | enum `Rol` | `OFICIAL_LOGISTICA`, `COMANDANTE_UNIDAD`, `JEFE_LOGISTICA_GU`, `JEFE_ALMACEN`, `ALMACENERO`, `AUDITOR` (`JEFE_LOGISTICA_COLOGE` y `ADMINISTRADOR` en incrementos posteriores) |
| organo_id | uuid FK → organo | coherente con el rol: oficial/comandante → `UNIDAD`; jefe GU → `GRAN_UNIDAD`; jefe de almacén/almacenero → `SERVICIO` |
| almacen_id | uuid FK → almacen, nulo | obligatorio para jefe de almacén y almacenero |
| activo | bool | |

## 3. Inventario (módulo `inventory`)

### stock
| Campo | Tipo | Reglas |
|---|---|---|
| almacen_id | uuid FK | PK compuesta (almacen_id, item_id) |
| item_id | uuid FK | |
| cantidad | integer | `CHECK (cantidad >= 0)` |
| actualizado_en | timestamptz | |

### movimiento (inmutable)
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| almacen_id, item_id | uuid FK | |
| tipo | enum | `ENTRADA` (seed inicial), `SALIDA_DESPACHO` |
| cantidad | integer | > 0 |
| requerimiento_id | uuid FK, nulo | obligatorio en `SALIDA_DESPACHO` |
| usuario_id | uuid FK | |
| ocurrido_en | timestamptz | |

**Invariante (EQ-03)**: `stock.cantidad = Σ ENTRADA − Σ SALIDA_DESPACHO` por (almacén, ítem).

## 4. Requerimientos (módulo `requests`)

### requerimiento
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| codigo | text único | legible, p. ej. `REQ-2026-000123` |
| unidad_id | uuid FK → organo (`UNIDAD`) | unidad del oficial que lo registra (FR-006) |
| gran_unidad_id | uuid FK → organo (`GRAN_UNIDAD`) | copiado del padre de la unidad al crear; filtra la jurisdicción |
| almacen_id | uuid FK → almacen | el de la categoría (FR-006, FR-007) |
| categoria | enum `Categoria` | todos los ítems de la misma categoría |
| estado | enum `EstadoRequerimiento` | ver §6 |
| monto_total | numeric(14,2) | Σ cantidad × valor_unitario, calculado al enviar |
| creado_por | uuid FK → usuario | |
| creado_en, actualizado_en | timestamptz | |
| version | integer | aumenta en cada transición |

### item_requerimiento
| Campo | Tipo | Reglas |
|---|---|---|
| requerimiento_id | uuid FK | PK compuesta (requerimiento_id, item_id): sin ítems repetidos |
| item_id | uuid FK | activo y de la categoría del requerimiento |
| cantidad_solicitada | integer | > 0 |
| cantidad_despachada | integer, nulo | 0 ≤ x ≤ cantidad_solicitada; se fija al despachar |
| cantidad_recibida | integer, nulo | ≥ 0; se fija en el acta |
| observacion | text, nulo | diferencias de la recepción |

Los ítems solo pueden cambiar en `BORRADOR`. Después, lo despachado y lo recibido se escriben una
única vez en el caso de uso de despacho y en el del acta.

**Protección del acta (FR-023)**: además de la regla del dominio, un disparador rechaza cualquier
`UPDATE` o `DELETE` sobre `requerimiento` e `item_requerimiento` cuando el requerimiento está en un
estado final (CONFIRMADA, RECHAZADA o ANULADA). Así, un acta firmada solo se puede alterar
desactivando el disparador a propósito, que es lo que hace la prueba de EQ-02, y en ese caso la
verificación responde ALTERADA.

### historial_requerimiento (inmutable)
| Campo | Tipo | Reglas |
|---|---|---|
| id | bigserial PK | |
| requerimiento_id | uuid FK | |
| accion | enum | `CREAR`, `ENVIAR`, `ENVIO_BLOQUEADO`, `FIRMAR`, `RECHAZAR`, `ANULAR`, `DESPACHAR`, `FIRMAR_ACTA` |
| estado_anterior | enum, nulo | |
| estado_nuevo | enum | igual al anterior en `ENVIO_BLOQUEADO` |
| usuario_id | uuid FK | |
| rol | enum `Rol` | copia al momento |
| organo_id | uuid FK | copia al momento |
| motivo | text, nulo | obligatorio en `RECHAZAR`, `ANULAR` y `ENVIO_BLOQUEADO` |
| ocurrido_en | timestamptz | |

## 5. Firma digital (módulo `signing`) y Auditoría (módulo `audit`)

### firma (inmutable)
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| requerimiento_id | uuid FK | |
| nivel | enum `NivelFirma` | `VB_UNIDAD`, `CONFORMIDAD_GU`, `APROBACION_ALMACEN`, `ACTA_RECEPCION` (`AUTORIZACION_COLOGE` en 002) |
| decision | enum | `APROBAR`, `RECHAZAR` (el acta siempre `APROBAR`) |
| firmante_id | uuid FK → usuario | |
| rol, organo_id | copia al momento | |
| contenido_canonico | text | JSON canónico firmado (research §3) |
| huella_sha256 | char(64) | hex |
| firma | text | Ed25519 en base64 |
| metodo | text | `ed25519-sha256-v1` |
| clave_id | text | identificador de la clave del sistema |
| firmado_en | timestamptz | |

**Única** `(requerimiento_id, nivel)`: cada nivel firma una sola vez (RN02, FR-013).

### acta_recepcion (inmutable)
| Campo | Tipo | Reglas |
|---|---|---|
| id | uuid PK | |
| requerimiento_id | uuid FK único | una acta por requerimiento |
| firma_id | uuid FK → firma (`ACTA_RECEPCION`) | |
| tiene_diferencias | bool | algún ítem con recibido ≠ despachado |
| creado_en | timestamptz | |

La verificación reconstruye el contenido canónico desde `requerimiento`, `item_requerimiento` y
los datos de la firma, recalcula la huella y comprueba la firma con la clave pública. Si algo no
coincide, el resultado es `ALTERADA`.

### registro_auditoria (inmutable)
| Campo | Tipo | Reglas |
|---|---|---|
| id | bigserial PK | |
| tipo_evento | text | p. ej. `REQUERIMIENTO.FIRMAR`, `INVENTARIO.DESPACHO` |
| entidad, entidad_id | text, uuid | |
| usuario_id, rol, organo_id | | |
| datos | jsonb | resumen del evento |
| huella_anterior | char(64) | huella del registro anterior (`0…0` en el primero) |
| huella | char(64) | SHA-256(huella_anterior + JSON canónico del registro) |
| ocurrido_en | timestamptz | |

## 6. Estados y transiciones (`EstadoRequerimiento`)

La máquina de estados vive en `dominio/requerimiento.py` (patrón State, ADR-007). Cualquier
transición que no esté en la tabla lanza `TransicionNoPermitida`, que la API devuelve como 409.

| Desde | Acción | Rol (y órgano) | Hacia | Firma | Condición |
|---|---|---|---|---|---|
| — | crear | OFICIAL_LOGISTICA | BORRADOR | — | ≥ 1 ítem, una sola categoría |
| BORRADOR | editar | OFICIAL_LOGISTICA (misma unidad) | BORRADOR | — | |
| BORRADOR | enviar | OFICIAL_LOGISTICA (misma unidad) | PENDIENTE_VB_UNIDAD | — | `ReglaAprobacion` no exige COLOGE |
| BORRADOR | enviar | OFICIAL_LOGISTICA | BORRADOR (bloqueado) | — | material de guerra o monto ≥ umbral → `ENVIO_BLOQUEADO` (FR-012) |
| BORRADOR | anular | OFICIAL_LOGISTICA (misma unidad) | ANULADA | — | motivo obligatorio (FR-022) |
| PENDIENTE_VB_UNIDAD | firmar | COMANDANTE_UNIDAD (misma unidad) | PENDIENTE_CONFORMIDAD | VB_UNIDAD | |
| PENDIENTE_CONFORMIDAD | firmar | JEFE_LOGISTICA_GU (gran_unidad_id) | PENDIENTE_APROBACION | CONFORMIDAD_GU | (en 002: → PENDIENTE_AUTORIZACION_COLOGE o APROBADA según reglas) |
| PENDIENTE_APROBACION | firmar | JEFE_ALMACEN (almacen_id) | APROBADA | APROBACION_ALMACEN | |
| PENDIENTE_VB_UNIDAD / PENDIENTE_CONFORMIDAD / PENDIENTE_APROBACION | rechazar | firmante del nivel | RECHAZADA | nivel con `RECHAZAR` | motivo obligatorio |
| APROBADA | despachar | ALMACENERO (almacen_id) | EN_TRANSITO | — | 0 ≤ despachado ≤ solicitado y ≤ stock; ≥ 1 ítem con despachado > 0 |
| EN_TRANSITO | firmar acta | OFICIAL_LOGISTICA (misma unidad) | CONFIRMADA | ACTA_RECEPCION | recibido por cada ítem |

Estados finales: CONFIRMADA, RECHAZADA, ANULADA. `PENDIENTE_AUTORIZACION_COLOGE` existe en el enum
pero no se alcanza en 001.

**Regla de aprobación (`dominio/regla_aprobacion.py`, RN03)**:
`requiere_cologe = categoria == MATERIAL_GUERRA or monto_total >= UMBRAL_MONTO_ALTO`. El umbral se
lee de la configuración (ADR-008); valor por defecto ficticio: 50 000,00.

## 7. Visibilidad por rol (FR-002)

| Rol | Ve los requerimientos donde… |
|---|---|
| OFICIAL_LOGISTICA, COMANDANTE_UNIDAD | `unidad_id = usuario.organo_id` (el comandante no ve los `BORRADOR`) |
| JEFE_LOGISTICA_GU | `gran_unidad_id = usuario.organo_id` y estado ≠ BORRADOR |
| JEFE_ALMACEN, ALMACENERO | `almacen_id = usuario.almacen_id` y estado ∈ {PENDIENTE_APROBACION, APROBADA, EN_TRANSITO, CONFIRMADA} o rechazado en su nivel |
| AUDITOR | todos, solo lectura y verificación |

Fuera de esa regla, la solicitud responde 404.

## 8. Índices para las consultas críticas

| Consulta | Índice |
|---|---|
| Bandeja de la unidad por estado, recientes primero | `requerimiento (unidad_id, estado, creado_en DESC)` |
| Bandeja de la Gran Unidad | `requerimiento (gran_unidad_id, estado, creado_en DESC)` |
| Bandeja del almacén | `requerimiento (almacen_id, estado, creado_en DESC)` |
| Línea de tiempo | `historial_requerimiento (requerimiento_id, ocurrido_en)` |
| Firmas de un requerimiento | único `firma (requerimiento_id, nivel)` |
| Movimientos por stock (invariante EQ-03) | `movimiento (almacen_id, item_id)` |
| Catálogo por categoría | `item (categoria) WHERE activo` |
| Inicio de sesión | único `usuario (usuario)` |
| Último registro de la cadena | PK `registro_auditoria (id)` |

Los listados se paginan con `page` y `size` (máximo 50). `codigo` e `id` también son únicos.

## 9. Seeds (datos ficticios, RC13)

- 2 Grandes Unidades (`1DE`, `2DE`), con 2 unidades cada una.
- 1 servicio de Intendencia y 1 de Material de Guerra, cada uno con un almacén.
- 10 ítems de intendencia y 4 de material de guerra, con valor unitario.
- Stock inicial registrado como movimientos `ENTRADA`.
- Usuarios por rol: oficial y comandante de cada unidad, jefe de logística de cada Gran Unidad,
  jefe de almacén y almacenero de cada almacén, y un auditor.
- Contraseña común de demostración, que se toma de una variable de entorno y nunca se versiona.
- El script es idempotente: no duplica datos si se ejecuta dos veces.
