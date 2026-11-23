"""Entidades del catálogo (data-model.md §1). Python puro e inmutables."""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.modules.catalog.dominio.tipos import Categoria, TipoOrgano


@dataclass(frozen=True)
class Organo:
    id: uuid.UUID
    codigo: str
    nombre: str
    tipo: TipoOrgano
    padre_id: uuid.UUID | None


@dataclass(frozen=True)
class Item:
    id: uuid.UUID
    codigo: str
    nombre: str
    categoria: Categoria
    unidad_medida: str
    valor_unitario: Decimal
    activo: bool


@dataclass(frozen=True)
class Almacen:
    id: uuid.UUID
    nombre: str
    organo_id: uuid.UUID
    categoria: Categoria
