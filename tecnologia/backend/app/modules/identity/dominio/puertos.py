"""Puertos del módulo de identidad (inversión de dependencias, segregación de interfaces)."""

import uuid
from typing import Protocol

from app.modules.identity.dominio.usuario import OrganoResumen, Usuario


class RepositorioUsuarios(Protocol):
    def por_nombre(self, usuario: str) -> Usuario | None: ...

    def por_id(self, usuario_id: uuid.UUID) -> Usuario | None: ...


class VerificadorContrasenas(Protocol):
    def verificar(self, contrasena: str, hash_guardado: str | None) -> bool:
        """Con ``hash_guardado`` None devuelve False, tardando lo mismo que una verificación."""
        ...


class ConsultaOrganos(Protocol):
    """Datos del órgano del usuario; los provee el módulo de catálogo."""

    def resumen(self, organo_id: uuid.UUID) -> OrganoResumen | None: ...


class EmisorTokens(Protocol):
    def emitir(self, usuario: Usuario) -> tuple[str, int]:
        """Devuelve el token y su duración en segundos."""
        ...
