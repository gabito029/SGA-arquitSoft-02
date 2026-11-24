"""Tipos de columna compartidos por los modelos de SQLAlchemy de todos los módulos."""

from enum import StrEnum
from functools import cache

from sqlalchemy import Enum


@cache
def enum_pg(clase: type[StrEnum], nombre: str) -> Enum:
    """Enum nativo de PostgreSQL que guarda el *valor* de cada miembro.

    Se devuelve siempre el mismo objeto por nombre, porque varios módulos comparten el tipo
    (por ejemplo, ``rol`` y ``categoria``). Los tipos los crea la migración, no ``create_all``.
    """
    return Enum(
        clase,
        name=nombre,
        values_callable=lambda miembros: [m.value for m in miembros],
        validate_strings=True,
        create_type=False,
    )
