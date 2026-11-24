"""Autenticación con JWT y autorización por rol (ADR-006, research §4, EQ-01).

- Sin token, o con un token inválido o expirado: 401.
- Con un rol que no puede realizar la acción: 403.
- La jurisdicción (unidad, Gran Unidad, almacén) se valida en cada caso de uso: lo ajeno es 404.

La API no guarda estado de sesión: todo lo necesario viaja firmado en el token.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import obtener_configuracion
from app.core.errores import NoAutenticado, SinPermiso

ALGORITMO = "HS256"

esquema_bearer = HTTPBearer(
    auto_error=False,
    description="Token JWT obtenido en POST /api/v1/auth/login",
)


@dataclass(frozen=True)
class UsuarioActual:
    id: uuid.UUID
    rol: str
    organo_id: uuid.UUID
    almacen_id: uuid.UUID | None


@dataclass(frozen=True)
class TokenEmitido:
    token: str
    expira_en: int  # segundos


def crear_token(
    *,
    usuario_id: uuid.UUID,
    rol: str,
    organo_id: uuid.UUID,
    almacen_id: uuid.UUID | None,
    minutos: int | None = None,
) -> TokenEmitido:
    configuracion = obtener_configuracion()
    duracion = timedelta(minutes=configuracion.jwt_minutos if minutos is None else minutos)
    ahora = datetime.now(UTC)
    carga = {
        "sub": str(usuario_id),
        "rol": str(rol),
        "organo_id": str(organo_id),
        "almacen_id": str(almacen_id) if almacen_id else None,
        "iat": int(ahora.timestamp()),
        "exp": int((ahora + duracion).timestamp()),
    }
    token = jwt.encode(carga, configuracion.jwt_secreto, algorithm=ALGORITMO)
    return TokenEmitido(token=token, expira_en=int(duracion.total_seconds()))


def decodificar_token(token: str) -> UsuarioActual:
    configuracion = obtener_configuracion()
    try:
        carga = jwt.decode(
            token,
            configuracion.jwt_secreto,
            algorithms=[ALGORITMO],
            options={"require": ["sub", "rol", "organo_id", "exp"]},
        )
        almacen = carga.get("almacen_id")
        return UsuarioActual(
            id=uuid.UUID(carga["sub"]),
            rol=carga["rol"],
            organo_id=uuid.UUID(carga["organo_id"]),
            almacen_id=uuid.UUID(almacen) if almacen else None,
        )
    except jwt.ExpiredSignatureError as error:
        raise NoAutenticado("La sesión expiró. Inicie sesión de nuevo.") from error
    except (jwt.PyJWTError, ValueError, KeyError) as error:
        raise NoAutenticado("El token de sesión no es válido.") from error


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
) -> UsuarioActual:
    """Dependencia de FastAPI: exige un JWT válido en ``Authorization: Bearer``."""
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise NoAutenticado()
    return decodificar_token(credenciales.credentials)


def requiere_rol(*roles: StrEnum | str) -> Callable[..., UsuarioActual]:
    """Dependencia de FastAPI que además exige uno de los roles dados (403 si no)."""
    permitidos = frozenset(str(r) for r in roles)

    def _dependencia(usuario: UsuarioActual = Depends(usuario_actual)) -> UsuarioActual:
        if usuario.rol not in permitidos:
            raise SinPermiso()
        return usuario

    return _dependencia
