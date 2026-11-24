"""Caso de uso: consultar el catálogo (ítems activos y estructura orgánica), con caché.

Research §7.

Es el servicio público del módulo ``catalog``: los demás módulos lo usan a él, nunca sus tablas.
"""

import uuid

from app.modules.catalog.aplicacion.cache_ttl import CacheTTL
from app.modules.catalog.dominio.entidades import Almacen, Item, Organo
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

    def items_por_id(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, Item]:
        """Ítems por id, activos o no. Sin caché: el estado ``activo`` se lee siempre al día."""
        return {i.id: i for i in self._repositorio.obtener_items(list(set(ids)))}

    def almacen_por_categoria(self, categoria: Categoria) -> Almacen | None:
        def calcular() -> Almacen | None:
            return self._repositorio.almacen_por_categoria(categoria)

        if self._cache is None:
            return calcular()
        return self._cache.obtener_o_calcular(("almacen_categoria", categoria), calcular)

    def almacen(self, almacen_id: uuid.UUID) -> Almacen | None:
        def calcular() -> Almacen | None:
            return self._repositorio.obtener_almacen(almacen_id)

        if self._cache is None:
            return calcular()
        return self._cache.obtener_o_calcular(("almacen", almacen_id), calcular)
