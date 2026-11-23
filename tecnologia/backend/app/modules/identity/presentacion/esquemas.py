"""Esquemas de entrada y salida de identidad (contracts/openapi.yaml: Token, Usuario)."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.identity.dominio.rol import Rol
from app.modules.identity.dominio.usuario import PerfilUsuario


class CredencialesEntrada(BaseModel):
    usuario: str = Field(min_length=1, max_length=100)
    contrasena: str = Field(min_length=1, max_length=200)


class OrganoResumenSalida(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str


class UsuarioSalida(BaseModel):
    id: uuid.UUID
    usuario: str
    nombre_completo: str
    rol: Rol
    organo: OrganoResumenSalida
    almacen_id: uuid.UUID | None

    @classmethod
    def desde_perfil(cls, perfil: PerfilUsuario) -> "UsuarioSalida":
        return cls(
            id=perfil.id,
            usuario=perfil.usuario,
            nombre_completo=perfil.nombre_completo,
            rol=perfil.rol,
            organo=OrganoResumenSalida(
                id=perfil.organo.id, codigo=perfil.organo.codigo, nombre=perfil.organo.nombre
            ),
            almacen_id=perfil.almacen_id,
        )


class TokenSalida(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expira_en: int = Field(description="Segundos")
    usuario: UsuarioSalida
