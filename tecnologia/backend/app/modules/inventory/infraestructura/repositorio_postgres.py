"""Adaptador del stock y los movimientos sobre PostgreSQL. Trabaja en la sesión de quien llama."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.inventory.dominio.puertos import Movimiento, SaldoStock
from app.modules.inventory.infraestructura.modelos import MovimientoModelo, StockModelo


class RepositorioStockPostgres:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def bloquear(self, almacen_id: uuid.UUID, item_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        cantidades: dict[uuid.UUID, int] = {}
        # Una fila por vez y en el orden recibido (por item_id): evita interbloqueos.
        for item_id in item_ids:
            cantidad = self._sesion.scalar(
                select(StockModelo.cantidad)
                .where(StockModelo.almacen_id == almacen_id, StockModelo.item_id == item_id)
                .with_for_update()
            )
            cantidades[item_id] = cantidad or 0
        return cantidades

    def descontar(self, almacen_id: uuid.UUID, item_id: uuid.UUID, cantidad: int) -> None:
        self._sesion.execute(
            update(StockModelo)
            .where(StockModelo.almacen_id == almacen_id, StockModelo.item_id == item_id)
            .values(cantidad=StockModelo.cantidad - cantidad, actualizado_en=datetime.now(UTC))
        )

    def registrar_movimiento(self, movimiento: Movimiento) -> None:
        self._sesion.add(
            MovimientoModelo(
                almacen_id=movimiento.almacen_id,
                item_id=movimiento.item_id,
                tipo=movimiento.tipo,
                cantidad=movimiento.cantidad,
                requerimiento_id=movimiento.requerimiento_id,
                usuario_id=movimiento.usuario_id,
            )
        )
        self._sesion.flush()

    def listar(self, almacen_id: uuid.UUID, page: int, size: int) -> tuple[list[SaldoStock], int]:
        total = self._sesion.scalar(
            select(func.count())
            .select_from(StockModelo)
            .where(StockModelo.almacen_id == almacen_id)
        )
        filas = self._sesion.execute(
            select(StockModelo.item_id, StockModelo.cantidad)
            .where(StockModelo.almacen_id == almacen_id)
            .order_by(StockModelo.item_id)
            .offset((page - 1) * size)
            .limit(size)
        )
        return [SaldoStock(item_id=f.item_id, cantidad=f.cantidad) for f in filas], total or 0
