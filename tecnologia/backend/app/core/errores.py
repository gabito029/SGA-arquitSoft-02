"""Errores de negocio con su código HTTP y su ``codigo`` del contrato (esquema ``Error``).

Este archivo es Python puro, sin FastAPI: el dominio puede lanzar estos errores sin depender del
framework (constitución, principio V). Los manejadores que los convierten en respuestas HTTP están
en ``app/core/manejadores_errores.py``.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DetalleError:
    campo: str
    mensaje: str


class ErrorNegocio(Exception):
    estado_http: int = 400
    codigo_por_defecto: str = "ERROR_NEGOCIO"
    mensaje_por_defecto: str = "No se pudo completar la operación."

    def __init__(
        self,
        mensaje: str | None = None,
        *,
        codigo: str | None = None,
        detalles: list[DetalleError] | None = None,
    ) -> None:
        self.mensaje = mensaje or self.mensaje_por_defecto
        self.codigo = codigo or self.codigo_por_defecto
        self.detalles = detalles or []
        super().__init__(self.mensaje)


class NoAutenticado(ErrorNegocio):
    estado_http = 401
    codigo_por_defecto = "NO_AUTENTICADO"
    mensaje_por_defecto = "Debe iniciar sesión para continuar."


class SinPermiso(ErrorNegocio):
    estado_http = 403
    codigo_por_defecto = "SIN_PERMISO"
    mensaje_por_defecto = "Su rol no permite realizar esta acción."


class NoEncontrado(ErrorNegocio):
    estado_http = 404
    codigo_por_defecto = "NO_ENCONTRADO"
    mensaje_por_defecto = "El recurso no existe o no pertenece a su jurisdicción."


class Conflicto(ErrorNegocio):
    """Regla de negocio violada (409). Las subclases fijan su ``codigo`` del contrato."""

    estado_http = 409
    codigo_por_defecto = "CONFLICTO"
    mensaje_por_defecto = "La operación entra en conflicto con el estado actual."


class Validacion(ErrorNegocio):
    estado_http = 422
    codigo_por_defecto = "VALIDACION"
    mensaje_por_defecto = "Los datos enviados no son válidos."
