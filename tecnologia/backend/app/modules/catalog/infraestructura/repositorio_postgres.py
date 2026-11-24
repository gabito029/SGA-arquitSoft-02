"""Adaptador del repositorio del catálogo sobre PostgreSQL (patrón Repository)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.dominio.entidades import Almacen, Item, Organo
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.catalog.infraestructura.modelos import AlmacenModelo, ItemModelo, OrganoModelo


def _item(m: ItemModelo) -> Item:
    return Item(
        id=m.id,
        codigo=m.codigo,
        nombre=m.nombre,
        categoria=m.categoria,
        unidad_medida=m.unidad_medida,
        valor_unitario=m.valor_unitario,
        activo=m.activo,
    )


def _almacen(m: AlmacenModelo) -> Almacen:
    return Almacen(id=m.id, nombre=m.nombre, organo_id=m.organo_id, categoria=m.categoria)


class RepositorioCatalogoPostgres:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def listar_items_activos(self, categoria: Categoria | None) -> list[Item]:
        consulta = select(ItemModelo).where(ItemModelo.activo.is_(True))
        if categoria is not None:
            consulta = consulta.where(ItemModelo.categoria == categoria)
        consulta = consulta.order_by(ItemModelo.codigo)
        return [_item(m) for m in self._sesion.scalars(consulta)]

    def obtener_items(self, ids: list[uuid.UUID]) -> list[Item]:
        if not ids:
            return []
        consulta = select(ItemModelo).where(ItemModelo.id.in_(ids))
        return [_item(m) for m in self._sesion.scalars(consulta)]

    def almacen_por_categoria(self, categoria: Categoria) -> Almacen | None:
        m = self._sesion.scalar(
            select(AlmacenModelo)
            .where(AlmacenModelo.categoria == categoria)
            .order_by(AlmacenModelo.nombre)
            .limit(1)
        )
        return _almacen(m) if m else None

    def obtener_almacen(self, almacen_id: uuid.UUID) -> Almacen | None:
        m = self._sesion.get(AlmacenModelo, almacen_id)
        return _almacen(m) if m else None

    def obtener_organo(self, organo_id: uuid.UUID) -> Organo | None:
        m = self._sesion.get(OrganoModelo, organo_id)
        if m is None:
            return None
        return Organo(id=m.id, codigo=m.codigo, nombre=m.nombre, tipo=m.tipo, padre_id=m.padre_id)
