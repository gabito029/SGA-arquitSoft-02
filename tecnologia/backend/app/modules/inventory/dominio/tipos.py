"""Tipos del inventario (data-model.md movimiento.tipo). Python puro."""

from enum import StrEnum


class TipoMovimiento(StrEnum):
    ENTRADA = "ENTRADA"
    SALIDA_DESPACHO = "SALIDA_DESPACHO"
