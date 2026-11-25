"""T011: generador de PDF con ReportLab (research §8 de 002)."""

import re
from dataclasses import replace

from app.modules.signing.dominio.documento import (
    LineaDocumento,
    TipoDocumento,
    extraer_codigo,
    generar_codigo,
)
from app.modules.signing.dominio.tipos import DecisionFirma
from app.modules.signing.infraestructura.generador_pdf_reportlab import (
    GeneradorPdfReportLab,
    huella_corta,
)
from tests.unitarias.test_documento import documento, sello


def _paginas(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf))


def test_genera_un_pdf_con_el_codigo_en_los_metadatos():
    codigo = generar_codigo()
    rechazo = replace(sello(minuto=3), decision=DecisionFirma.RECHAZAR, motivo="Sin stock & <otro>")
    d = documento(sello(), rechazo)
    pdf = GeneradorPdfReportLab().generar(d, codigo, d.huella_contenido())
    assert pdf.startswith(b"%PDF-")
    assert extraer_codigo(pdf) == codigo
    assert _paginas(pdf) == 1


def test_muchos_items_ocupan_varias_paginas():
    lineas = tuple(
        LineaDocumento(f"INT-{i:03}", f"Ítem de prueba <{i}> & más", "UND", "INTENDENCIA", i + 1)
        for i in range(120)
    )
    d = replace(documento(sello()), lineas=lineas)
    pdf = GeneradorPdfReportLab().generar(d, generar_codigo(), d.huella_contenido())
    assert _paginas(pdf) >= 2


def test_acta_sin_sellos():
    d = replace(
        documento(),
        tipo=TipoDocumento.ACTA,
        lineas=(LineaDocumento("INT-001", "Ración", "UND", "INTENDENCIA", 10, 10, 9, "Falta 1"),),
        tiene_diferencias=True,
    )
    assert GeneradorPdfReportLab().generar(d, generar_codigo(), "b" * 64).startswith(b"%PDF-")


def test_huella_corta():
    assert huella_corta("0123456789abcdef" * 4) == "01234567…89abcdef"
    assert huella_corta("corta") == "corta"
