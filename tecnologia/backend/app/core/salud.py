"""Verificación de estado ``/health`` (ADR-013): la usan Docker y, en 002, Uptime Kuma (EQ-06)."""

import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.base_datos import obtener_motor

registro = logging.getLogger(__name__)

router = APIRouter(tags=["Salud"])


class EstadoSalud(BaseModel):
    estado: Literal["OK"]
    base_datos: Literal["OK", "ERROR"]


@router.get(
    "/health",
    response_model=EstadoSalud,
    summary="Estado de la API y de la conexión a la base de datos (ADR-013)",
)
def salud() -> EstadoSalud:
    try:
        with obtener_motor().connect() as conexion:
            conexion.execute(text("SELECT 1"))
        base_datos: Literal["OK", "ERROR"] = "OK"
    except Exception:  # cualquier fallo de conexión se informa como ERROR
        registro.warning("La base de datos no responde", exc_info=True)
        base_datos = "ERROR"
    return EstadoSalud(estado="OK", base_datos=base_datos)
