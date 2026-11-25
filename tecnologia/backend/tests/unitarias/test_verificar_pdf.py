"""T036 (EQ-02, prueba unitaria): verificación de un PDF subido con el firmador Ed25519 real de la
librería ``cryptography``. Cambiar un byte del PDF firmado hace que la firma ya no sea válida."""

import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.core.errores import NoEncontrado
from app.modules.signing.aplicacion.emitir_documento import EmitirDocumento
from app.modules.signing.aplicacion.verificar_pdf import (
    MOTIVO_AUTENTICO,
    MOTIVO_BYTES,
    MOTIVO_CODIGO_DESCONOCIDO,
    MOTIVO_FIRMAS,
    MOTIVO_SIN_CODIGO,
    VerificarPdf,
)
from app.modules.signing.dominio.contenido_canonico import huella_sha256
from app.modules.signing.dominio.documento import generar_codigo
from app.modules.signing.dominio.tipos import ResultadoPdf
from app.modules.signing.infraestructura.firmador_ed25519 import FirmadorEd25519
from app.modules.signing.infraestructura.generador_pdf_reportlab import GeneradorPdfReportLab
from tests.dobles_documentos import AlmacenEnMemoria, RepositorioDocumentosEnMemoria
from tests.unitarias.test_documento import documento, sello


@pytest.fixture(scope="module")
def firmador():
    return FirmadorEd25519(Ed25519PrivateKey.generate())


@pytest.fixture
def emitido(firmador):
    """Un PDF real (ReportLab) emitido y firmado con Ed25519."""
    repositorio = RepositorioDocumentosEnMemoria()
    emitir = EmitirDocumento(repositorio, AlmacenEnMemoria(), GeneradorPdfReportLab(), firmador)
    fila, pdf = emitir.ejecutar(documento(sello()), uuid.uuid4(), uuid.uuid4())
    return repositorio, fila, pdf


def permitir(_documento) -> None:
    return None


def integras(_documento) -> bool:
    return True


def test_un_pdf_sin_cambios_es_autentico(firmador, emitido):
    repositorio, fila, pdf = emitido
    resultado = VerificarPdf(repositorio, firmador).ejecutar(pdf, permitir, integras)
    assert resultado.resultado is ResultadoPdf.AUTENTICO
    assert resultado.motivo == MOTIVO_AUTENTICO
    assert resultado.documento == fila


@pytest.mark.parametrize("posicion", [0.25, 0.5, 0.9])
def test_cambiar_un_byte_invalida_la_firma_ed25519(firmador, emitido, posicion):
    repositorio, fila, pdf = emitido
    i = int(len(pdf) * posicion)
    alterado = pdf[:i] + bytes([pdf[i] ^ 0x01]) + pdf[i + 1 :]
    # Si el byte cambiado cae dentro del código, el código ya no se reconoce: también ALTERADO.
    assert not firmador.verificar(alterado, fila.firma, fila.clave_id)
    assert huella_sha256(alterado) != fila.huella_sha256
    resultado = VerificarPdf(repositorio, firmador).ejecutar(alterado, permitir, integras)
    assert resultado.resultado is ResultadoPdf.ALTERADO
    assert resultado.motivo in (MOTIVO_BYTES, MOTIVO_CODIGO_DESCONOCIDO, MOTIVO_SIN_CODIGO)


def test_un_byte_agregado_al_final_tambien_es_alterado(firmador, emitido):
    repositorio, _, pdf = emitido
    resultado = VerificarPdf(repositorio, firmador).ejecutar(pdf + b"\n", permitir, integras)
    assert (resultado.resultado, resultado.motivo) == (ResultadoPdf.ALTERADO, MOTIVO_BYTES)


def test_un_pdf_sin_codigo_no_es_del_sga(firmador, emitido):
    repositorio, _, _ = emitido
    resultado = VerificarPdf(repositorio, firmador).ejecutar(b"%PDF-1.4 ajeno", permitir, integras)
    assert (resultado.resultado, resultado.motivo) == (ResultadoPdf.ALTERADO, MOTIVO_SIN_CODIGO)
    assert resultado.documento is None


def test_un_codigo_desconocido_es_alterado(firmador, emitido):
    repositorio, _, _ = emitido
    falso = f"%PDF-1.4 {generar_codigo()}".encode()
    resultado = VerificarPdf(repositorio, firmador).ejecutar(falso, permitir, integras)
    assert resultado.motivo == MOTIVO_CODIGO_DESCONOCIDO


def test_firmas_alteradas_en_la_base_hacen_alterado_el_pdf(firmador, emitido):
    repositorio, _, pdf = emitido
    resultado = VerificarPdf(repositorio, firmador).ejecutar(pdf, permitir, lambda _d: False)
    assert (resultado.resultado, resultado.motivo) == (ResultadoPdf.ALTERADO, MOTIVO_FIRMAS)


def test_sin_acceso_al_requerimiento_responde_404(firmador, emitido):
    repositorio, _, pdf = emitido

    def denegar(_documento) -> None:
        raise NoEncontrado()

    with pytest.raises(NoEncontrado):
        VerificarPdf(repositorio, firmador).ejecutar(pdf, denegar, integras)
