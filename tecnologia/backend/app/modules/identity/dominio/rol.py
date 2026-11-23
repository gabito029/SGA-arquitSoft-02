"""Roles del sistema (data-model.md usuario.rol; docs/01-analisis-de-sistema/01-actores.md).

Los actores son siempre personas con un rol (constitución, principio X). JEFE_LOGISTICA_COLOGE y
ADMINISTRADOR llegan en incrementos posteriores.
"""

from enum import StrEnum


class Rol(StrEnum):
    OFICIAL_LOGISTICA = "OFICIAL_LOGISTICA"
    COMANDANTE_UNIDAD = "COMANDANTE_UNIDAD"
    JEFE_LOGISTICA_GU = "JEFE_LOGISTICA_GU"
    JEFE_ALMACEN = "JEFE_ALMACEN"
    ALMACENERO = "ALMACENERO"
    AUDITOR = "AUDITOR"


ROLES_DE_ALMACEN = frozenset({Rol.JEFE_ALMACEN, Rol.ALMACENERO})
