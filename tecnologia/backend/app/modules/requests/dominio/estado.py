"""Estados del requerimiento (data-model.md requerimiento.estado y §6; ADR-007). Python puro."""

from enum import StrEnum


class EstadoRequerimiento(StrEnum):
    BORRADOR = "BORRADOR"
    PENDIENTE_VB_UNIDAD = "PENDIENTE_VB_UNIDAD"
    PENDIENTE_CONFORMIDAD = "PENDIENTE_CONFORMIDAD"
    # Existe en el enum, pero no se alcanza en el incremento 001 (FR-012).
    PENDIENTE_AUTORIZACION_COLOGE = "PENDIENTE_AUTORIZACION_COLOGE"
    PENDIENTE_APROBACION = "PENDIENTE_APROBACION"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    ANULADA = "ANULADA"
    EN_TRANSITO = "EN_TRANSITO"
    CONFIRMADA = "CONFIRMADA"


ESTADOS_FINALES = frozenset(
    {EstadoRequerimiento.CONFIRMADA, EstadoRequerimiento.RECHAZADA, EstadoRequerimiento.ANULADA}
)


class AccionHistorial(StrEnum):
    """Acciones de la línea de tiempo (data-model.md historial_requerimiento.accion)."""

    CREAR = "CREAR"
    ENVIAR = "ENVIAR"
    ENVIO_BLOQUEADO = "ENVIO_BLOQUEADO"
    FIRMAR = "FIRMAR"
    RECHAZAR = "RECHAZAR"
    ANULAR = "ANULAR"
    DESPACHAR = "DESPACHAR"
    FIRMAR_ACTA = "FIRMAR_ACTA"


ACCIONES_CON_MOTIVO = frozenset(
    {AccionHistorial.RECHAZAR, AccionHistorial.ANULAR, AccionHistorial.ENVIO_BLOQUEADO}
)
