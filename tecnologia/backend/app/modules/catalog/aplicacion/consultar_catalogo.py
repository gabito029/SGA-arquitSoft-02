"""Caso de uso: consultar el catálogo (ítems activos y estructura orgánica), con caché.

Research §7.

Es el servicio público del módulo ``catalog``: los demás módulos lo usan a él, nunca sus tablas.
"""

import uuid

from app.modules.catalog.aplicacion.cache_ttl import CacheTTL
from app.modules.catalog.dominio.entidades import Item, Organo
from app.modules.catalog.dominio.puertos import RepositorioCatalogo
from app.modules.catalog.dominio.tipos import Categoria

SEGUNDOS_CACHE = 300


class ConsultarCatalogo:
    def __init__(self, repositorio: RepositorioCatalogo, cache: CacheTTL | None) -> None:
        self._repositorio = repositorio
        self._cache = cache

    def items_activos(self, categoria: Categoria | None = None) -> list[Item]:
        def calcular() -> list[Item]:
            return self._repositorio.listar_items_activos(categoria)

        if self._cache is None:
            return calcular()
        return list(self._cache.obtener_o_calcular(("items", categoria), calcular))

    def organo(self, organo_id: uuid.UUID) -> Organo | None:
        def calcular() -> Organo | None:
            return self._repositorio.obtener_organo(organo_id)

        if self._cache is None:
            return calcular()
        return self._cache.obtener_o_calcular(("organo", organo_id), calcular)
