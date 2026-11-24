"""Composición del inventario: el servicio público de despacho con su repositorio."""

from sqlalchemy.orm import Session

from app.modules.inventory.aplicacion.servicio_despacho import ServicioDespacho
from app.modules.inventory.infraestructura.repositorio_postgres import RepositorioStockPostgres


def construir_servicio_despacho(sesion: Session) -> ServicioDespacho:
    return ServicioDespacho(RepositorioStockPostgres(sesion))
