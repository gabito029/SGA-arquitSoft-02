"""T006: dominio de documentos de 002 (código de verificación y huella del contenido)."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from app.modules.signing.dominio.documento import (
    ALFABETO_CODIGO,
    DocumentoPdf,
    LineaDocumento,
    Referencia,
    SelloDocumento,
    TipoDocumento,
    clave_almacen,
    es_codigo_valido,
    extraer_codigo,
    generar_codigo,
)
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma

AHORA = datetime(2026, 11, 24, 15, 0, tzinfo=UTC)


def sello(nivel=NivelFirma.VB_UNIDAD, minuto=0) -> SelloDocumento:
    return SelloDocumento(
        firma_id=uuid.uuid4(),
        nivel=nivel,
        decision=DecisionFirma.APROBAR,
        firmante="Comandante BIM-11",
        rol="COMANDANTE_UNIDAD",
        organo=Referencia("BIM-11", "BIM N.° 11"),
        firmado_en=AHORA.replace(minute=minuto),
        metodo="ed25519-sha256-v1",
        huella_sha256="a" * 64,
    )


def documento(*sellos: SelloDocumento) -> DocumentoPdf:
    return DocumentoPdf(
        tipo=TipoDocumento.REQUERIMIENTO,
        requerimiento_id=uuid.UUID(int=1),
        numero="REQ-2026-000001",
        unidad=Referencia("BIM-11", "BIM N.° 11"),
        gran_unidad=Referencia("1DE", "1.ª División de Ejército"),
        almacen=Referencia("SINTE", "Almacén de intendencia"),
        fecha=AHORA,
        lineas=(LineaDocumento("INT-001", "Ración", "UND", "INTENDENCIA", 10),),
        sellos=sellos,
    )


def test_el_codigo_tiene_el_formato_y_es_aleatorio():
    codigos = {generar_codigo() for _ in range(200)}
    assert len(codigos) == 200
    for codigo in codigos:
        assert es_codigo_valido(codigo)
        assert codigo.startswith("SGA-") and len(codigo) == 18
        assert set(codigo.replace("SGA-", "").replace("-", "")) <= set(ALFABETO_CODIGO)


@pytest.mark.parametrize(
    "codigo",
    ["SGA-AAAA-AAAA-AAA", "SGA-AAAA-AAAA-AAA0", "XYZ-AAAA-AAAA-AAAA", "SGA-AAAA-AAAA-AAAÑ"],
)
def test_codigos_invalidos(codigo):
    assert not es_codigo_valido(codigo)


def test_extraer_codigo_de_los_bytes():
    codigo = generar_codigo()
    contenido = b"%PDF-1.4 ... /Keywords (SGA-VERIFICACION " + codigo.encode() + b")"
    assert extraer_codigo(contenido) == codigo
    assert extraer_codigo(b"%PDF-1.4 sin codigo") is None


def test_la_huella_del_contenido_es_estable_y_detecta_cambios():
    s = sello()
    original = documento(s)
    assert original.huella_contenido() == documento(s).huella_contenido()
    linea = replace(original.lineas[0], cantidad_solicitada=11)
    assert replace(original, lineas=(linea,)).huella_contenido() != original.huella_contenido()


def test_ultima_firma_y_firmas_incluidas():
    primero, segundo = sello(minuto=1), sello(NivelFirma.CONFORMIDAD_GU, minuto=5)
    d = documento(primero, segundo)
    assert d.ultima_firma_id == segundo.firma_id
    assert d.firmas_incluidas == (primero.firma_id, segundo.firma_id)
    assert documento().ultima_firma_id is None


def test_clave_del_almacen():
    assert clave_almacen(uuid.UUID(int=1), TipoDocumento.ACTA, "SGA-AAAA-BBBB-CCCC") == (
        "00000000-0000-0000-0000-000000000001/acta-SGA-AAAA-BBBB-CCCC.pdf"
    )
