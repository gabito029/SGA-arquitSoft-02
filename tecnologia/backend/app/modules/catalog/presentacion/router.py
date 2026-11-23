"""Endpoints del catálogo (contracts/openapi.yaml → /api/v1/catalogo)."""

import uuid

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.core.seguridad import UsuarioActual, usuario_actual
from app.core.unidad_trabajo import FabricaUnidadTrabajo, obtener_fabrica_uow
from app.modules.catalog.aplicacion.consultar_catalogo import SEGUNDOS_CACHE
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.catalog.infraestructura.dependencias import construir_consulta_catalogo

router = APIRouter(prefix="/api/v1/catalogo", tags=["Catálogo"])


class ItemSalida(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    categoria: Categoria
    unidad_medida: str
    valor_unitario: str  # decimal como texto, p. ej. "35.50"


@router.get(
    "/items",
    response_model=list[ItemSalida],
    summary="Ítems activos del catálogo (con caché de 300 s)",
)
def listar_items(
    response: Response,
    categoria: Categoria | None = None,
    _: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> list[ItemSalida]:
    with fabrica_uow() as uow:
        items = construir_consulta_catalogo(uow.sesion).items_activos(categoria)
    response.headers["Cache-Control"] = f"private, max-age={SEGUNDOS_CACHE}"
    return [
        ItemSalida(
            id=i.id,
            codigo=i.codigo,
            nombre=i.nombre,
            categoria=i.categoria,
            unidad_medida=i.unidad_medida,
            valor_unitario=f"{i.valor_unitario:.2f}",
        )
        for i in items
    ]
