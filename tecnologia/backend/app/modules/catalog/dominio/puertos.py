"""Puertos del catálogo. Los casos de uso dependen de estas interfaces, no de SQLAlchemy."""

import uuid
from typing import Protocol

from app.modules.catalog.dominio.entidades import Almacen, Item, Organo
from app.modules.catalog.dominio.tipos import Categoria


class RepositorioCatalogo(Protocol):
    def listar_items_activos(self, categoria: Categoria | None) -> list[Item]: ...

    def obtener_organo(self, organo_id: uuid.UUID) -> Organo | None: ...

    def obtener_items(self, ids: list[uuid.UUID]) -> list[Item]:
        """Ítems con esos ids, activos o no (las solicitudes existentes siguen su curso)."""
        ...

    def almacen_por_categoria(self, categoria: Categoria) -> Almacen | None: ...

    def obtener_almacen(self, almacen_id: uuid.UUID) -> Almacen | None: ...
