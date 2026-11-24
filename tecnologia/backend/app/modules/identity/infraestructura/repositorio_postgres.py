"""Adaptador del repositorio de usuarios sobre PostgreSQL."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.dominio.usuario import Usuario
from app.modules.identity.infraestructura.modelos import UsuarioModelo


def _a_entidad(m: UsuarioModelo) -> Usuario:
    return Usuario(
        id=m.id,
        usuario=m.usuario,
        nombre_completo=m.nombre_completo,
        hash_contrasena=m.hash_contrasena,
        rol=m.rol,
        organo_id=m.organo_id,
        almacen_id=m.almacen_id,
        activo=m.activo,
    )


class RepositorioUsuariosPostgres:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def por_nombre(self, usuario: str) -> Usuario | None:
        m = self._sesion.scalar(select(UsuarioModelo).where(UsuarioModelo.usuario == usuario))
        return _a_entidad(m) if m else None

    def por_id(self, usuario_id: uuid.UUID) -> Usuario | None:
        m = self._sesion.get(UsuarioModelo, usuario_id)
        return _a_entidad(m) if m else None
