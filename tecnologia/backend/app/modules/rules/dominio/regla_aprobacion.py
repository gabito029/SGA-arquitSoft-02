"""Reglas de aprobación configurables (ADR-008; RN03). Patrón Strategy (plan → SOLID).

``requests`` depende solo del protocolo ``ReglaAprobacion``: en 002 se agrega la aprobación
automática (RN04) como otra estrategia, sin tocar ``requests`` (lo que mide EQ-07).
"""

from decimal import Decimal
from typing import Protocol

from app.modules.catalog.dominio.tipos import Categoria


class ReglaAprobacion(Protocol):
    def requiere_cologe(self, categoria: Categoria, monto_total: Decimal) -> bool: ...


class ReglaCologePorCategoriaOMonto:
    """RN03: exige la autorización del COLOGE para material de guerra o monto alto.

    ``requiere_cologe = categoria == MATERIAL_GUERRA or monto_total >= umbral`` (data-model.md §6).
    """

    def __init__(self, umbral_monto_alto: Decimal) -> None:
        if umbral_monto_alto < 0:
            raise ValueError("El umbral de monto alto no puede ser negativo")
        self._umbral = umbral_monto_alto

    def requiere_cologe(self, categoria: Categoria, monto_total: Decimal) -> bool:
        return categoria == Categoria.MATERIAL_GUERRA or monto_total >= self._umbral
