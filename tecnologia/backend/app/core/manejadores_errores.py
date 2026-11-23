"""Convierte los errores en respuestas con el esquema ``Error`` del contrato:
``{"codigo": ..., "mensaje": ... (en español), "detalles": [{"campo", "mensaje"}]}``.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errores import ErrorNegocio, NoAutenticado

registro = logging.getLogger(__name__)

# Mensajes en español para los errores de validación de Pydantic más comunes.
MENSAJES_VALIDACION: dict[str, str] = {
    "missing": "Este campo es obligatorio.",
    "string_type": "Debe ser un texto.",
    "string_too_short": "Es demasiado corto.",
    "string_too_long": "Es demasiado largo.",
    "int_type": "Debe ser un número entero.",
    "int_parsing": "Debe ser un número entero.",
    "int_from_float": "Debe ser un número entero.",
    "bool_parsing": "Debe ser verdadero o falso.",
    "greater_than": "Debe ser mayor que {gt}.",
    "greater_than_equal": "Debe ser mayor o igual que {ge}.",
    "less_than": "Debe ser menor que {lt}.",
    "less_than_equal": "Debe ser menor o igual que {le}.",
    "too_short": "Debe tener al menos {min_length} elemento(s).",
    "too_long": "Debe tener como máximo {max_length} elemento(s).",
    "enum": "Valor no permitido. Valores válidos: {expected}.",
    "literal_error": "Valor no permitido. Valores válidos: {expected}.",
    "uuid_parsing": "Debe ser un identificador válido.",
    "uuid_type": "Debe ser un identificador válido.",
    "json_invalid": "El cuerpo de la petición no es un JSON válido.",
    "model_attributes_type": "Debe ser un objeto.",
    "list_type": "Debe ser una lista.",
    "decimal_parsing": "Debe ser un número.",
}

MENSAJES_HTTP: dict[int, tuple[str, str]] = {
    404: ("NO_ENCONTRADO", "El recurso solicitado no existe."),
    405: ("METODO_NO_PERMITIDO", "El método HTTP no está permitido en este recurso."),
}


def _cuerpo(codigo: str, mensaje: str, detalles: list[dict[str, str]] | None = None) -> dict:
    return {"codigo": codigo, "mensaje": mensaje, "detalles": detalles or []}


def _mensaje_validacion(error: dict[str, Any]) -> str:
    plantilla = MENSAJES_VALIDACION.get(error.get("type", ""))
    if plantilla is None:
        return "Valor no válido."
    try:
        return plantilla.format(**(error.get("ctx") or {}))
    except (KeyError, IndexError):
        return plantilla


def _campo(ubicacion: tuple | list) -> str:
    partes = [str(p) for p in ubicacion if p not in ("body", "query", "path")]
    return ".".join(partes) or "cuerpo"


async def _manejar_error_negocio(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, ErrorNegocio)
    detalles = [{"campo": d.campo, "mensaje": d.mensaje} for d in error.detalles]
    cabeceras = {"WWW-Authenticate": "Bearer"} if isinstance(error, NoAutenticado) else None
    return JSONResponse(
        status_code=error.estado_http,
        content=_cuerpo(error.codigo, error.mensaje, detalles),
        headers=cabeceras,
    )


async def _manejar_validacion(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    detalles = [
        {"campo": _campo(e.get("loc", ())), "mensaje": _mensaje_validacion(e)}
        for e in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_cuerpo("VALIDACION", "Los datos enviados no son válidos.", detalles),
    )


async def _manejar_http(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, StarletteHTTPException)
    codigo, mensaje = MENSAJES_HTTP.get(
        error.status_code, ("ERROR_HTTP", "No se pudo completar la petición.")
    )
    return JSONResponse(
        status_code=error.status_code,
        content=_cuerpo(codigo, mensaje),
        headers=getattr(error, "headers", None),
    )


async def _manejar_inesperado(_: Request, error: Exception) -> JSONResponse:
    registro.exception("Error no controlado", exc_info=error)
    return JSONResponse(
        status_code=500,
        content=_cuerpo("ERROR_INTERNO", "Ocurrió un error inesperado. Intente de nuevo."),
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorNegocio, _manejar_error_negocio)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    app.add_exception_handler(Exception, _manejar_inesperado)
