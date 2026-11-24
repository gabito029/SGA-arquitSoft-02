"""Errores del dominio de requerimientos, con el ``codigo`` del contrato. Python puro."""

from app.core.errores import Conflicto, Validacion


class TransicionNoPermitida(Conflicto):
    codigo_por_defecto = "TRANSICION_NO_PERMITIDA"
    mensaje_por_defecto = "La acción no está permitida en el estado actual del requerimiento."


class NivelYaFirmado(Conflicto):
    codigo_por_defecto = "NIVEL_YA_FIRMADO"
    mensaje_por_defecto = "Este nivel del conducto regular ya firmó el requerimiento."


class EstadoCambiado(Conflicto):
    codigo_por_defecto = "ESTADO_CAMBIADO"
    mensaje_por_defecto = (
        "Otro usuario cambió el requerimiento mientras se procesaba su acción. "
        "Actualice la página e intente de nuevo."
    )


class RequiereCologe(Conflicto):
    codigo_por_defecto = "REQUIERE_COLOGE"
    mensaje_por_defecto = "Requiere autorización del COLOGE (disponible en un próximo incremento)."


class MotivoObligatorio(Validacion):
    codigo_por_defecto = "MOTIVO_OBLIGATORIO"
    mensaje_por_defecto = "Debe indicar el motivo."


class CantidadInvalida(Validacion):
    codigo_por_defecto = "CANTIDAD_INVALIDA"
    mensaje_por_defecto = "Una o más cantidades no son válidas."


class ItemsInvalidos(Validacion):
    codigo_por_defecto = "ITEMS_INVALIDOS"
    mensaje_por_defecto = "Los ítems de la solicitud no son válidos."
