"""Adaptador del repositorio del catálogo sobre PostgreSQL (patrón Repository)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.dominio.entidades import Item, Organo
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.catalog.infraestructura.modelos import ItemModelo, OrganoModelo


class RepositorioCatalogoPostgres:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def listar_items_activos(self, categoria: Categoria | None) -> list[Item]:
        consulta = select(ItemModelo).where(ItemModelo.activo.is_(True))
        if categoria is not None:
            consulta = consulta.where(ItemModelo.categoria == categoria)
        consulta = consulta.order_by(ItemModelo.codigo)
        return [
            Item(
                id=m.id,
                codigo=m.codigo,
                nombre=m.nombre,
                categoria=m.categoria,
                unidad_medida=m.unidad_medida,
                valor_unitario=m.valor_unitario,
                activo=m.activo,
            )
            for m in self._sesion.scalars(consulta)
        ]

    def obtener_organo(self, organo_id: uuid.UUID) -> Organo | None:
        m = self._sesion.get(OrganoModelo, organo_id)
        if m is None:
            return None
        return Organo(id=m.id, codigo=m.codigo, nombre=m.nombre, tipo=m.tipo, padre_id=m.padre_id)
