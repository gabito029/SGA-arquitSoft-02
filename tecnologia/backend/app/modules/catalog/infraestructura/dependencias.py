"""Composición del módulo de catálogo: arma el caso de uso con sus adaptadores."""

from sqlalchemy.orm import Session

from app.core.config import obtener_configuracion
from app.modules.catalog.aplicacion.cache_ttl import CacheTTL
from app.modules.catalog.aplicacion.consultar_catalogo import SEGUNDOS_CACHE, ConsultarCatalogo
from app.modules.catalog.infraestructura.repositorio_postgres import RepositorioCatalogoPostgres

# Una sola caché por proceso, compartida por todas las peticiones.
CACHE_CATALOGO = CacheTTL(SEGUNDOS_CACHE)


def construir_consulta_catalogo(sesion: Session) -> ConsultarCatalogo:
    # CATALOGO_CACHE_ACTIVA=false la desactiva, para medir EQ-04 con y sin caché (T092).
    cache = CACHE_CATALOGO if obtener_configuracion().catalogo_cache_activa else None
    return ConsultarCatalogo(RepositorioCatalogoPostgres(sesion), cache)
