"""Errores del inventario, con el ``codigo`` del contrato. Python puro."""

from app.core.errores import Conflicto


class StockInsuficiente(Conflicto):
    codigo_por_defecto = "STOCK_INSUFICIENTE"
    mensaje_por_defecto = "No hay stock suficiente en el almacén para despachar estas cantidades."
