"""Casos de uso de identidad: iniciar sesión (HU01, RF01) y consultar el perfil propio."""

import uuid
from dataclasses import dataclass

from app.core.errores import NoAutenticado
from app.modules.identity.dominio.puertos import (
    ConsultaOrganos,
    EmisorTokens,
    RepositorioUsuarios,
    VerificadorContrasenas,
)
from app.modules.identity.dominio.usuario import PerfilUsuario, Usuario

# Mismo mensaje para usuario inexistente, inactivo o contraseña errónea: no revela cuál falló.
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."


@dataclass(frozen=True)
class SesionIniciada:
    token: str
    expira_en: int
    perfil: PerfilUsuario


def _perfil(usuario: Usuario, organos: ConsultaOrganos) -> PerfilUsuario:
    organo = organos.resumen(usuario.organo_id)
    if organo is None:
        # Datos inconsistentes: el usuario no puede operar (caso límite de spec.md).
        raise NoAutenticado(MENSAJE_CREDENCIALES)
    return PerfilUsuario(
        id=usuario.id,
        usuario=usuario.usuario,
        nombre_completo=usuario.nombre_completo,
        rol=usuario.rol,
        organo=organo,
        almacen_id=usuario.almacen_id,
    )


class IniciarSesion:
    def __init__(
        self,
        usuarios: RepositorioUsuarios,
        verificador: VerificadorContrasenas,
        organos: ConsultaOrganos,
        emisor: EmisorTokens,
    ) -> None:
        self._usuarios = usuarios
        self._verificador = verificador
        self._organos = organos
        self._emisor = emisor

    def ejecutar(self, nombre_usuario: str, contrasena: str) -> SesionIniciada:
        usuario = self._usuarios.por_nombre(nombre_usuario.strip())
        # Se verifica aunque el usuario no exista (hash None), para que el tiempo de respuesta
        # no delate qué nombres de usuario existen.
        hash_guardado = usuario.hash_contrasena if usuario else None
        contrasena_valida = self._verificador.verificar(contrasena, hash_guardado)
        if usuario is None or not usuario.activo or not contrasena_valida:
            raise NoAutenticado(MENSAJE_CREDENCIALES)
        perfil = _perfil(usuario, self._organos)
        token, expira_en = self._emisor.emitir(usuario)
        return SesionIniciada(token=token, expira_en=expira_en, perfil=perfil)


class ConsultarPerfil:
    def __init__(self, usuarios: RepositorioUsuarios, organos: ConsultaOrganos) -> None:
        self._usuarios = usuarios
        self._organos = organos

    def ejecutar(self, usuario_id: uuid.UUID) -> PerfilUsuario:
        usuario = self._usuarios.por_id(usuario_id)
        if usuario is None or not usuario.activo:
            raise NoAutenticado("La sesión ya no es válida. Inicie sesión de nuevo.")
        return _perfil(usuario, self._organos)
