"""Política de acceso a los requerimientos (FR-002, FR-003; data-model.md §6 y §7).

- **Visibilidad**: qué requerimientos ve cada rol. Lo que no ve responde 404, como si no existiera.
- **Acciones disponibles**: qué puede hacer el usuario actual sobre un requerimiento que sí ve;
  la interfaz solo muestra estas (FR-029 y contrato ``acciones_disponibles``).

El rol permitido para cada endpoint lo exige además el router (403). Aquí no hay FastAPI ni SQL.
"""

import uuid
from dataclasses import dataclass
from enum import StrEnum

from app.core.errores import NoEncontrado
from app.modules.identity.dominio.rol import ROLES_DE_ALMACEN, Rol
from app.modules.requests.dominio.estado import EstadoRequerimiento
from app.modules.requests.dominio.puertos import FiltroVisibilidad
from app.modules.requests.dominio.requerimiento import Requerimiento

E = EstadoRequerimiento


@dataclass(frozen=True)
class Actor:
    """Quién actúa: lo que viaja firmado en el JWT (sub, rol, organo_id, almacen_id)."""

    id: uuid.UUID
    rol: Rol
    organo_id: uuid.UUID
    almacen_id: uuid.UUID | None


class Accion(StrEnum):
    EDITAR = "EDITAR"
    ENVIAR = "ENVIAR"
    ANULAR = "ANULAR"
    FIRMAR = "FIRMAR"
    RECHAZAR = "RECHAZAR"
    DESPACHAR = "DESPACHAR"
    FIRMAR_ACTA = "FIRMAR_ACTA"


# data-model.md §7: el almacén ve lo que llega a su nivel y lo que sigue después.
ESTADOS_VISIBLES_ALMACEN = frozenset(
    {E.PENDIENTE_APROBACION, E.APROBADA, E.EN_TRANSITO, E.CONFIRMADA}
)

MENSAJE_NO_ENCONTRADO = "La solicitud no existe o no pertenece a su jurisdicción."


def filtro_visibilidad(actor: Actor) -> FiltroVisibilidad:
    """Traduce la tabla de data-model.md §7 a un filtro que el repositorio aplica en SQL."""
    if actor.rol is Rol.OFICIAL_LOGISTICA:
        return FiltroVisibilidad("unidad_id", actor.organo_id, incluir_borradores=True)
    if actor.rol is Rol.COMANDANTE_UNIDAD:
        return FiltroVisibilidad("unidad_id", actor.organo_id, incluir_borradores=False)
    if actor.rol is Rol.JEFE_LOGISTICA_GU:
        return FiltroVisibilidad("gran_unidad_id", actor.organo_id, incluir_borradores=False)
    if actor.rol in ROLES_DE_ALMACEN:
        if actor.almacen_id is None:
            return FiltroVisibilidad(None, None, incluir_borradores=False, ninguno=True)
        return FiltroVisibilidad(
            "almacen_id",
            actor.almacen_id,
            incluir_borradores=False,
            estados=ESTADOS_VISIBLES_ALMACEN,
            rechazados_desde=E.PENDIENTE_APROBACION,
        )
    if actor.rol is Rol.AUDITOR:
        return FiltroVisibilidad(None, None, incluir_borradores=False)
    return FiltroVisibilidad(None, None, incluir_borradores=False, ninguno=True)


def puede_ver(
    actor: Actor, req: Requerimiento, rechazado_desde: EstadoRequerimiento | None = None
) -> bool:
    """Misma regla que ``filtro_visibilidad``, aplicada a un requerimiento ya cargado."""
    filtro = filtro_visibilidad(actor)
    if filtro.ninguno:
        return False
    if filtro.campo is not None and getattr(req, filtro.campo) != filtro.valor:
        return False
    if req.estado is E.BORRADOR and not filtro.incluir_borradores:
        return False
    if filtro.estados is not None and req.estado not in filtro.estados:
        return (
            req.estado is E.RECHAZADA
            and filtro.rechazados_desde is not None
            and rechazado_desde == filtro.rechazados_desde
        )
    return True


def exigir_visible(
    actor: Actor, req: Requerimiento | None, rechazado_desde: EstadoRequerimiento | None = None
) -> Requerimiento:
    """Devuelve el requerimiento o lanza 404 si no existe o no es de su jurisdicción (FR-003)."""
    if req is None or not puede_ver(actor, req, rechazado_desde):
        raise NoEncontrado(MENSAJE_NO_ENCONTRADO)
    return req


def acciones_disponibles(actor: Actor, req: Requerimiento) -> list[Accion]:
    """Acciones de data-model.md §6 que este usuario puede ejecutar ahora sobre ``req``."""
    misma_unidad = req.unidad_id == actor.organo_id
    mismo_almacen = actor.almacen_id is not None and req.almacen_id == actor.almacen_id
    estado = req.estado

    if actor.rol is Rol.OFICIAL_LOGISTICA and misma_unidad:
        if estado is E.BORRADOR:
            return [Accion.EDITAR, Accion.ENVIAR, Accion.ANULAR]
        if estado is E.EN_TRANSITO:
            return [Accion.FIRMAR_ACTA]
    firma_su_nivel = (
        (estado is E.PENDIENTE_VB_UNIDAD and actor.rol is Rol.COMANDANTE_UNIDAD and misma_unidad)
        or (
            estado is E.PENDIENTE_CONFORMIDAD
            and actor.rol is Rol.JEFE_LOGISTICA_GU
            and req.gran_unidad_id == actor.organo_id
        )
        or (estado is E.PENDIENTE_APROBACION and actor.rol is Rol.JEFE_ALMACEN and mismo_almacen)
    )
    if firma_su_nivel:
        return [Accion.FIRMAR, Accion.RECHAZAR]
    if estado is E.APROBADA and actor.rol is Rol.ALMACENERO and mismo_almacen:
        return [Accion.DESPACHAR]
    return []
