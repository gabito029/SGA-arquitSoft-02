"""Puertos del catálogo. Los casos de uso dependen de estas interfaces, no de SQLAlchemy."""

import uuid
from typing import Protocol

from app.modules.catalog.dominio.entidades import Item, Organo
from app.modules.catalog.dominio.tipos import Categoria


class RepositorioCatalogo(Protocol):
    def listar_items_activos(self, categoria: Categoria | None) -> list[Item]: ...

    def obtener_organo(self, organo_id: uuid.UUID) -> Organo | None: ...
