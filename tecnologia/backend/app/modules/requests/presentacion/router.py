"""Endpoints de requerimientos de la US1 (contracts/openapi.yaml → /api/v1/requerimientos).

Cada petición abre una Unidad de Trabajo: o se guarda todo (estado, ítems, historial, auditoría)
o no se guarda nada (ADR-003).
"""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.seguridad import UsuarioActual, requiere_rol, usuario_actual
from app.core.unidad_trabajo import FabricaUnidadTrabajo, obtener_fabrica_uow
from app.modules.identity.dominio.rol import Rol
from app.modules.requests.aplicacion.consultar_requerimientos import TAMANO_MAXIMO_PAGINA
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.estado import EstadoRequerimiento
from app.modules.requests.infraestructura.dependencias import (
    construir_consultar,
    construir_consultar_firmas,
    construir_enviar,
    construir_firmar,
    construir_registrar,
)
from app.modules.requests.presentacion.esquemas import (
    DecisionFirmaEntrada,
    FirmaSalida,
    PaginaRequerimientosSalida,
    RequerimientoEntrada,
    RequerimientoSalida,
)

router = APIRouter(prefix="/api/v1/requerimientos", tags=["Requerimientos"])

solo_oficial = requiere_rol(Rol.OFICIAL_LOGISTICA)
solo_firmantes = requiere_rol(Rol.COMANDANTE_UNIDAD, Rol.JEFE_LOGISTICA_GU, Rol.JEFE_ALMACEN)

_R401 = {401: {"description": "Sin sesión o token inválido/expirado"}}
_R403 = {403: {"description": "El rol del usuario no puede realizar esta acción"}}
_R404 = {404: {"description": "No existe o no pertenece a la jurisdicción del usuario"}}
_R409 = {
    409: {
        "description": "Regla de negocio: TRANSICION_NO_PERMITIDA, NIVEL_YA_FIRMADO, "
        "REQUIERE_COLOGE (envío bloqueado; queda ENVIO_BLOQUEADO en el historial) o "
        "ESTADO_CAMBIADO (acción concurrente)"
    }
}
_R422 = {422: {"description": "Datos de entrada inválidos (indica el campo y el motivo)"}}


def _actor(usuario: UsuarioActual) -> Actor:
    return Actor(
        id=usuario.id,
        rol=Rol(usuario.rol),
        organo_id=usuario.organo_id,
        almacen_id=usuario.almacen_id,
    )


@router.get(
    "",
    response_model=PaginaRequerimientosSalida,
    summary="Bandeja de requerimientos visibles para el usuario según su rol y órgano "
    "(FR-002, FR-029)",
    description="Aplica la visibilidad por rol de data-model.md §7. Los requerimientos en "
    "BORRADOR solo los ven los oficiales de logística de su unidad.",
    responses={**_R401, **_R422},
)
def listar(
    estado: EstadoRequerimiento | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=TAMANO_MAXIMO_PAGINA),
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> PaginaRequerimientosSalida:
    with fabrica_uow() as uow:
        pagina = construir_consultar(uow.sesion).bandeja(
            _actor(usuario), estado=estado, page=page, size=size
        )
    return PaginaRequerimientosSalida.desde_pagina(pagina)


@router.post(
    "",
    response_model=RequerimientoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un requerimiento en BORRADOR (HU02, RF02)",
    description="Solo OFICIAL_LOGISTICA. La unidad y el almacén se deducen del usuario y de la "
    "categoría de los ítems.",
    responses={**_R401, **_R403, **_R422},
)
def registrar(
    entrada: RequerimientoEntrada,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        req = construir_registrar(uow.sesion).registrar(actor, entrada.a_lineas())
        vista = construir_consultar(uow.sesion).detalle(actor, req.id)
    return RequerimientoSalida.desde_vista(vista)


@router.get(
    "/{id}",
    response_model=RequerimientoSalida,
    summary="Detalle del requerimiento con ítems y acciones disponibles para el usuario",
    responses={**_R401, **_R404},
)
def detalle(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    with fabrica_uow() as uow:
        vista = construir_consultar(uow.sesion).detalle(_actor(usuario), id)
    return RequerimientoSalida.desde_vista(vista)


@router.put(
    "/{id}",
    response_model=RequerimientoSalida,
    summary="Editar los ítems de un requerimiento en BORRADOR (FR-008)",
    responses={**_R401, **_R403, **_R404, **_R409, **_R422},
)
def editar(
    id: uuid.UUID,
    entrada: RequerimientoEntrada,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_registrar(uow.sesion).editar(actor, id, entrada.a_lineas())
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)


@router.post(
    "/{id}/enviar",
    response_model=RequerimientoSalida,
    summary="Enviar por el conducto regular (BORRADOR → PENDIENTE_VB_UNIDAD)",
    description="Aplica RN03. Si es de material de guerra o el monto alcanza el umbral, responde "
    "409 con codigo REQUIERE_COLOGE, registra ENVIO_BLOQUEADO en el historial y el estado no "
    "cambia (FR-012).",
    responses={**_R401, **_R403, **_R404, **_R409},
)
def enviar(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_enviar(uow).ejecutar(actor, id)
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)


# --- Firmas del conducto regular (US2) ---


@router.get(
    "/{id}/firmas",
    response_model=list[FirmaSalida],
    tags=["Firmas"],
    summary="Firmas registradas del requerimiento",
    responses={**_R401, **_R404},
)
def listar_firmas(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> list[FirmaSalida]:
    with fabrica_uow() as uow:
        vistas = construir_consultar_firmas(uow.sesion).ejecutar(_actor(usuario), id)
    return [FirmaSalida.desde_vista(v) for v in vistas]


@router.post(
    "/{id}/firmas",
    response_model=RequerimientoSalida,
    status_code=status.HTTP_201_CREATED,
    tags=["Firmas"],
    summary="Firmar (aprobar) o rechazar en el nivel actual del conducto regular "
    "(HU03, HU05, RF03, RF05)",
    description="El nivel se deduce del estado actual; el rol y el órgano del usuario deben "
    "corresponder a ese nivel. Rechazar exige motivo. Un nivel que ya firmó responde 409 "
    "NIVEL_YA_FIRMADO; un estado que no corresponde, 409 TRANSICION_NO_PERMITIDA; y una acción "
    "concurrente que llegó tarde, 409 ESTADO_CAMBIADO.",
    responses={**_R401, **_R403, **_R404, **_R409, **_R422},
)
def firmar(
    id: uuid.UUID,
    entrada: DecisionFirmaEntrada,
    usuario: UsuarioActual = Depends(solo_firmantes),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_firmar(uow.sesion).ejecutar(actor, id, entrada.decision, entrada.motivo)
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)
