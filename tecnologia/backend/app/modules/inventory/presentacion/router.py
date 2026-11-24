"""Endpoints del inventario (contracts/openapi.yaml → /api/v1/inventario)."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.seguridad import UsuarioActual, requiere_rol
from app.core.unidad_trabajo import FabricaUnidadTrabajo, obtener_fabrica_uow
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.catalog.infraestructura.dependencias import construir_consulta_catalogo
from app.modules.identity.dominio.rol import Rol
from app.modules.inventory.infraestructura.dependencias import construir_servicio_despacho

router = APIRouter(prefix="/api/v1/inventario", tags=["Inventario"])

TAMANO_MAXIMO_PAGINA = 50
roles_de_almacen = requiere_rol(Rol.JEFE_ALMACEN, Rol.ALMACENERO)


class ItemStockSalida(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    categoria: Categoria
    unidad_medida: str
    valor_unitario: str


class StockSalida(BaseModel):
    item: ItemStockSalida
    cantidad: int


class PaginaStockSalida(BaseModel):
    items: list[StockSalida]
    total: int
    page: int
    size: int


@router.get(
    "/stock",
    response_model=PaginaStockSalida,
    summary="Stock del almacén del usuario (JEFE_ALMACEN, ALMACENERO)",
    responses={
        401: {"description": "Sin sesión o token inválido/expirado"},
        403: {"description": "El rol del usuario no puede realizar esta acción"},
    },
)
def listar_stock(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=TAMANO_MAXIMO_PAGINA),
    usuario: UsuarioActual = Depends(roles_de_almacen),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> PaginaStockSalida:
    if usuario.almacen_id is None:
        return PaginaStockSalida(items=[], total=0, page=page, size=size)
    with fabrica_uow() as uow:
        saldos, total = construir_servicio_despacho(uow.sesion).stock(
            usuario.almacen_id, page, size
        )
        items = construir_consulta_catalogo(uow.sesion).items_por_id([s.item_id for s in saldos])
    return PaginaStockSalida(
        items=[
            StockSalida(
                item=ItemStockSalida(
                    id=i.id,
                    codigo=i.codigo,
                    nombre=i.nombre,
                    categoria=i.categoria,
                    unidad_medida=i.unidad_medida,
                    valor_unitario=f"{i.valor_unitario:.2f}",
                ),
                cantidad=s.cantidad,
            )
            for s in saldos
            if (i := items.get(s.item_id)) is not None
        ],
        total=total,
        page=page,
        size=size,
    )
