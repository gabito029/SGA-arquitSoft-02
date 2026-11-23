"""Correspondencia entre los estados pendientes y el nivel de firma del conducto regular
(data-model.md §6). Python puro."""

from app.modules.requests.dominio.estado import EstadoRequerimiento
from app.modules.signing.dominio.tipos import NivelFirma

# Estado pendiente → (nivel que firma, estado al que pasa si aprueba).
CONDUCTO_REGULAR: dict[EstadoRequerimiento, tuple[NivelFirma, EstadoRequerimiento]] = {
    EstadoRequerimiento.PENDIENTE_VB_UNIDAD: (
        NivelFirma.VB_UNIDAD,
        EstadoRequerimiento.PENDIENTE_CONFORMIDAD,
    ),
    # En 002, según las reglas, irá a PENDIENTE_AUTORIZACION_COLOGE o directo a APROBADA.
    EstadoRequerimiento.PENDIENTE_CONFORMIDAD: (
        NivelFirma.CONFORMIDAD_GU,
        EstadoRequerimiento.PENDIENTE_APROBACION,
    ),
    EstadoRequerimiento.PENDIENTE_APROBACION: (
        NivelFirma.APROBACION_ALMACEN,
        EstadoRequerimiento.APROBADA,
    ),
}


def nivel_de(estado: EstadoRequerimiento) -> NivelFirma | None:
    """Nivel que debe firmar en ``estado``, o None si el estado no espera una firma de nivel."""
    paso = CONDUCTO_REGULAR.get(estado)
    return paso[0] if paso else None
