"""T026: emisión de PDF firmados con dobles de los puertos (research §4 de 002; FR-010 a FR-013)."""

import hashlib
import uuid
from dataclasses import replace

import pytest

from app.modules.signing.aplicacion.emitir_documento import EmitirDocumento, SinFirmas
from app.modules.signing.dominio.errores import DocumentoInconsistente
from app.modules.signing.dominio.tipos import NivelFirma
from tests.dobles_documentos import AlmacenEnMemoria, GeneradorFalso, RepositorioDocumentosEnMemoria
from tests.firmador_falso import FirmadorFalso
from tests.unitarias.test_documento import documento, sello

EMISOR = uuid.UUID(int=7)
ORGANO = uuid.UUID(int=8)


def caso():
    repositorio, almacen, generador = (
        RepositorioDocumentosEnMemoria(),
        AlmacenEnMemoria(),
        GeneradorFalso(),
    )
    emitir = EmitirDocumento(repositorio, almacen, generador, FirmadorFalso())
    return emitir, repositorio, almacen, generador


def test_emite_firma_los_bytes_y_guarda_archivo_y_fila():
    emitir, repositorio, almacen, _ = caso()
    d = documento(sello())
    emitido, pdf = emitir.ejecutar(d, EMISOR, ORGANO)
    assert pdf.startswith(b"%PDF-")
    assert emitido.huella_sha256 == hashlib.sha256(pdf).hexdigest()
    assert FirmadorFalso().verificar(pdf, emitido.firma, emitido.clave_id)
    assert emitido.huella_contenido == d.huella_contenido()
    assert emitido.firmas_incluidas == d.firmas_incluidas
    assert emitido.ultima_firma_id == d.ultima_firma_id
    assert emitido.tamano_bytes == len(pdf)
    assert (emitido.emitido_por, emitido.organo_id) == (EMISOR, ORGANO)
    assert almacen.archivos[emitido.clave_almacen] == pdf
    assert repositorio.filas == [emitido]


def test_sin_firmas_no_hay_documento():
    emitir, *_ = caso()
    with pytest.raises(SinFirmas):
        emitir.ejecutar(documento(), EMISOR, ORGANO)


def test_reutiliza_el_documento_ya_emitido():
    emitir, repositorio, _, generador = caso()
    d = documento(sello())
    primero, pdf1 = emitir.ejecutar(d, EMISOR, ORGANO)
    segundo, pdf2 = emitir.ejecutar(d, EMISOR, ORGANO)
    assert segundo == primero and pdf2 == pdf1
    assert generador.generados == 1
    assert len(repositorio.filas) == 1


def test_una_firma_nueva_emite_otro_documento_y_conserva_el_anterior():
    emitir, repositorio, almacen, _ = caso()
    s1 = sello()
    primero, pdf1 = emitir.ejecutar(documento(s1), EMISOR, ORGANO)
    segundo, _ = emitir.ejecutar(
        documento(s1, sello(NivelFirma.CONFORMIDAD_GU, minuto=9)), EMISOR, ORGANO
    )
    assert segundo.codigo_verificacion != primero.codigo_verificacion
    assert len(repositorio.filas) == 2
    assert almacen.archivos[primero.clave_almacen] == pdf1


def test_emision_concurrente_devuelve_el_documento_del_otro():
    emitir, repositorio, almacen, _ = caso()
    d = documento(sello())
    # Otra petición emite el mismo estado firmado en paralelo y guarda su fila primero.
    ganador, pdf_ganador = EmitirDocumento(
        RepositorioDocumentosEnMemoria(), almacen, GeneradorFalso(), FirmadorFalso()
    ).ejecutar(d, EMISOR, ORGANO)
    repositorio.adelantarse = ganador
    emitido, pdf = emitir.ejecutar(d, EMISOR, ORGANO)
    assert emitido == ganador and pdf == pdf_ganador
    assert repositorio.filas == [ganador]


def test_no_entrega_un_archivo_que_no_coincide_con_su_huella():
    emitir, _, almacen, _ = caso()
    d = documento(sello())
    emitido, pdf = emitir.ejecutar(d, EMISOR, ORGANO)
    almacen.archivos[emitido.clave_almacen] = pdf.replace(b"%%EOF", b"%%EOX")
    with pytest.raises(DocumentoInconsistente):
        emitir.ejecutar(d, EMISOR, ORGANO)


def test_no_entrega_un_archivo_con_firma_que_no_corresponde():
    emitir, repositorio, _, _ = caso()
    d = documento(sello())
    emitido, _ = emitir.ejecutar(d, EMISOR, ORGANO)
    repositorio.filas[0] = replace(emitido, firma="otra-firma")
    with pytest.raises(DocumentoInconsistente):
        emitir.ejecutar(d, EMISOR, ORGANO)
