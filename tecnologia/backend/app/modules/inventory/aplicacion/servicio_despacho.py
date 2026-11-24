"""Servicio público de despacho del inventario (T068; ADR-003, research §5, EQ-03).

``despachar`` trabaja **dentro de la Unidad de Trabajo de quien lo llama**:

1. Bloquea las filas de ``stock`` con ``FOR UPDATE``, ordenadas por ``item_id`` para que dos
   despachos simultáneos no se interbloqueen.
2. Valida que haya stock suficiente para cada ítem; si falta en alguno, lanza
   ``StockInsuficiente`` (409) antes de escribir nada.
3. Registra un movimiento ``SALIDA_DESPACHO`` por ítem y descuenta el stock.

Así se mantiene el invariante: stock.cantidad = Σ ENTRADA − Σ SALIDA_DESPACHO por (almacén, ítem).
"""

import uuid

from app.core.errores import DetalleError
from app.modules.inventory.dominio.errores import StockInsuficiente
from app.modules.inventory.dominio.puertos import (
    LineaDespacho,
    Movimiento,
    RepositorioStock,
    SaldoStock,
)
from app.modules.inventory.dominio.tipos import TipoMovimiento


class ServicioDespacho:
    def __init__(self, repositorio: RepositorioStock) -> None:
        self._repositorio = repositorio

    def despachar(
        self,
        *,
        almacen_id: uuid.UUID,
        requerimiento_id: uuid.UUID,
        usuario_id: uuid.UUID,
        lineas: list[LineaDespacho],
    ) -> None:
        a_despachar = sorted(
            (li for li in lineas if li.cantidad > 0), key=lambda li: str(li.item_id)
        )
        disponibles = self._repositorio.bloquear(almacen_id, [li.item_id for li in a_despachar])
        faltantes = [
            DetalleError(
                f"items.{li.item_id}",
                f"Stock disponible: {disponibles.get(li.item_id, 0)}; solicitado: {li.cantidad}.",
            )
            for li in a_despachar
            if disponibles.get(li.item_id, 0) < li.cantidad
        ]
        if faltantes:
            raise StockInsuficiente(detalles=faltantes)
        for li in a_despachar:
            self._repositorio.registrar_movimiento(
                Movimiento(
                    almacen_id=almacen_id,
                    item_id=li.item_id,
                    tipo=TipoMovimiento.SALIDA_DESPACHO,
                    cantidad=li.cantidad,
                    requerimiento_id=requerimiento_id,
                    usuario_id=usuario_id,
                )
            )
            self._repositorio.descontar(almacen_id, li.item_id, li.cantidad)

    def stock(self, almacen_id: uuid.UUID, page: int, size: int) -> tuple[list[SaldoStock], int]:
        return self._repositorio.listar(almacen_id, page, size)
