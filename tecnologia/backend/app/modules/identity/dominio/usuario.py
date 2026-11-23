"""Entidades de identidad (data-model.md §2). Python puro."""

import uuid
from dataclasses import dataclass

from app.modules.identity.dominio.rol import Rol


@dataclass(frozen=True)
class Usuario:
    id: uuid.UUID
    usuario: str
    nombre_completo: str
    hash_contrasena: str
    rol: Rol
    organo_id: uuid.UUID
    almacen_id: uuid.UUID | None
    activo: bool


@dataclass(frozen=True)
class OrganoResumen:
    id: uuid.UUID
    codigo: str
    nombre: str


@dataclass(frozen=True)
class PerfilUsuario:
    """Lo que el usuario autenticado ve de sí mismo (esquema ``Usuario`` del contrato)."""

    id: uuid.UUID
    usuario: str
    nombre_completo: str
    rol: Rol
    organo: OrganoResumen
    almacen_id: uuid.UUID | None
