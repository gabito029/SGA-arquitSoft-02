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
    construir_enviar,
    construir_registrar,
)
from app.modules.requests.presentacion.esquemas import (
    PaginaRequerimientosSalida,
    RequerimientoEntrada,
    RequerimientoSalida,
)

router = APIRouter(prefix="/api/v1/requerimientos", tags=["Requerimientos"])

solo_oficial = requiere_rol(Rol.OFICIAL_LOGISTICA)

_R401 = {401: {"description": "Sin sesión o token inválido/expirado"}}
_R403 = {403: {"description": "El rol del usuario no puede realizar esta acción"}}
_R404 = {404: {"description": "No existe o no pertenece a la jurisdicción del usuario"}}
_R409 = {
    409: {
        "description": "Regla de negocio: TRANSICION_NO_PERMITIDA o REQUIERE_COLOGE (envío "
        "bloqueado; queda ENVIO_BLOQUEADO en el historial)"
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
