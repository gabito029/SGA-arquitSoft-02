"""Composición del módulo de identidad: arma los casos de uso con sus adaptadores."""

import uuid

from sqlalchemy.orm import Session

from app.core.seguridad import crear_token
from app.modules.catalog.aplicacion.consultar_catalogo import ConsultarCatalogo
from app.modules.catalog.infraestructura.dependencias import construir_consulta_catalogo
from app.modules.identity.aplicacion.iniciar_sesion import ConsultarPerfil, IniciarSesion
from app.modules.identity.dominio.usuario import OrganoResumen, Usuario
from app.modules.identity.infraestructura.hash_bcrypt import HasherBcrypt
from app.modules.identity.infraestructura.repositorio_postgres import RepositorioUsuariosPostgres


class ConsultaOrganosCatalogo:
    """Adaptador: obtiene el órgano a través del servicio público del módulo de catálogo."""

    def __init__(self, catalogo: ConsultarCatalogo) -> None:
        self._catalogo = catalogo

    def resumen(self, organo_id: uuid.UUID) -> OrganoResumen | None:
        organo = self._catalogo.organo(organo_id)
        if organo is None:
            return None
        return OrganoResumen(id=organo.id, codigo=organo.codigo, nombre=organo.nombre)


class EmisorTokensJwt:
    def emitir(self, usuario: Usuario) -> tuple[str, int]:
        emitido = crear_token(
            usuario_id=usuario.id,
            rol=usuario.rol,
            organo_id=usuario.organo_id,
            almacen_id=usuario.almacen_id,
        )
        return emitido.token, emitido.expira_en


def construir_iniciar_sesion(sesion: Session) -> IniciarSesion:
    return IniciarSesion(
        usuarios=RepositorioUsuariosPostgres(sesion),
        verificador=HasherBcrypt(),
        organos=ConsultaOrganosCatalogo(construir_consulta_catalogo(sesion)),
        emisor=EmisorTokensJwt(),
    )


def construir_consultar_perfil(sesion: Session) -> ConsultarPerfil:
    return ConsultarPerfil(
        usuarios=RepositorioUsuariosPostgres(sesion),
        organos=ConsultaOrganosCatalogo(construir_consulta_catalogo(sesion)),
    )
