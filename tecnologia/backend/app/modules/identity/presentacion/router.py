"""Endpoints de identidad (contracts/openapi.yaml → /api/v1/auth)."""

from fastapi import APIRouter, Depends

from app.core.seguridad import UsuarioActual, usuario_actual
from app.core.unidad_trabajo import FabricaUnidadTrabajo, obtener_fabrica_uow
from app.modules.identity.infraestructura.dependencias import (
    construir_consultar_perfil,
    construir_iniciar_sesion,
)
from app.modules.identity.presentacion.esquemas import (
    CredencialesEntrada,
    TokenSalida,
    UsuarioSalida,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Identidad"])

_ERRORES = {401: {"description": "Sin sesión o credenciales inválidas"}}


@router.post(
    "/login",
    response_model=TokenSalida,
    summary="Iniciar sesión (HU01, RF01)",
    responses={**_ERRORES, 422: {"description": "Datos de entrada inválidos"}},
)
def iniciar_sesion(
    credenciales: CredencialesEntrada,
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> TokenSalida:
    with fabrica_uow() as uow:
        sesion = construir_iniciar_sesion(uow.sesion).ejecutar(
            credenciales.usuario, credenciales.contrasena
        )
    return TokenSalida(
        access_token=sesion.token,
        expira_en=sesion.expira_en,
        usuario=UsuarioSalida.desde_perfil(sesion.perfil),
    )


@router.get(
    "/me",
    response_model=UsuarioSalida,
    summary="Datos del usuario autenticado (rol y órgano)",
    responses=_ERRORES,
)
def usuario_autenticado(
    actual: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> UsuarioSalida:
    with fabrica_uow() as uow:
        perfil = construir_consultar_perfil(uow.sesion).ejecutar(actual.id)
    return UsuarioSalida.desde_perfil(perfil)
