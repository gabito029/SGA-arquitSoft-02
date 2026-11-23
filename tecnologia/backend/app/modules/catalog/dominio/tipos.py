"""Tipos del catálogo (data-model.md §1). Python puro."""

from enum import StrEnum


class TipoOrgano(StrEnum):
    UNIDAD = "UNIDAD"
    GRAN_UNIDAD = "GRAN_UNIDAD"
    COLOGE = "COLOGE"
    SERVICIO = "SERVICIO"


class Categoria(StrEnum):
    INTENDENCIA = "INTENDENCIA"
    MATERIAL_GUERRA = "MATERIAL_GUERRA"
