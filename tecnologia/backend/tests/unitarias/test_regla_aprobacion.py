"""T033: regla RN03 (ReglaCologePorCategoriaOMonto)."""

from decimal import Decimal

import pytest

from app.modules.catalog.dominio.tipos import Categoria
from app.modules.rules.dominio.regla_aprobacion import ReglaCologePorCategoriaOMonto

UMBRAL = Decimal("50000.00")
regla = ReglaCologePorCategoriaOMonto(UMBRAL)


def test_intendencia_bajo_el_umbral_no_exige_cologe():
    assert regla.requiere_cologe(Categoria.INTENDENCIA, Decimal("49999.99")) is False


@pytest.mark.parametrize("monto", [Decimal("0"), Decimal("10.00"), Decimal("49999.99")])
def test_material_de_guerra_siempre_exige_cologe(monto):
    assert regla.requiere_cologe(Categoria.MATERIAL_GUERRA, monto) is True


@pytest.mark.parametrize("monto", [UMBRAL, Decimal("50000.01"), Decimal("120000")])
def test_intendencia_en_el_umbral_exacto_o_por_encima_exige_cologe(monto):
    assert regla.requiere_cologe(Categoria.INTENDENCIA, monto) is True


def test_el_umbral_no_puede_ser_negativo():
    with pytest.raises(ValueError):
        ReglaCologePorCategoriaOMonto(Decimal("-1"))
