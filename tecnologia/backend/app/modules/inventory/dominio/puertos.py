"""Puertos del inventario (inversión de dependencias). Python puro."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.modules.inventory.dominio.tipos import TipoMovimiento


@dataclass(frozen=True)
class LineaDespacho:
    item_id: uuid.UUID
    cantidad: int


@dataclass(frozen=True)
class Movimiento:
    almacen_id: uuid.UUID
    item_id: uuid.UUID
    tipo: TipoMovimiento
    cantidad: int
    requerimiento_id: uuid.UUID | None
    usuario_id: uuid.UUID


@dataclass(frozen=True)
class SaldoStock:
    item_id: uuid.UUID
    cantidad: int


class RepositorioStock(Protocol):
    def bloquear(self, almacen_id: uuid.UUID, item_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Bloquea (``FOR UPDATE``) las filas de stock **en el orden dado** y devuelve su cantidad.

        Un ítem sin fila de stock vale 0.
        """
        ...

    def descontar(self, almacen_id: uuid.UUID, item_id: uuid.UUID, cantidad: int) -> None: ...

    def registrar_movimiento(self, movimiento: Movimiento) -> None: ...

    def listar(self, almacen_id: uuid.UUID, page: int, size: int) -> tuple[list[SaldoStock], int]:
        """Página de saldos del almacén y el total de filas."""
        ...
