"""Servicio público de identidad: nombres de usuarios para mostrar quién firmó o actuó."""

import uuid

from app.modules.identity.dominio.puertos import RepositorioUsuarios


class ConsultarUsuarios:
    def __init__(self, usuarios: RepositorioUsuarios) -> None:
        self._usuarios = usuarios

    def nombres(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        resultado: dict[uuid.UUID, str] = {}
        for usuario_id in set(ids):
            usuario = self._usuarios.por_id(usuario_id)
            if usuario is not None:
                resultado[usuario_id] = usuario.nombre_completo
        return resultado
