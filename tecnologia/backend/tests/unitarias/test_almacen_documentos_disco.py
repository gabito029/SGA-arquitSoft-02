"""T009: adaptador de disco de ``AlmacenDocumentos`` (ADR-010)."""

import pytest

from app.modules.signing.dominio.errores import DocumentoExistente, DocumentoNoEncontrado
from app.modules.signing.infraestructura.almacen_documentos_disco import AlmacenDocumentosDisco


def test_guarda_y_lee(tmp_path):
    almacen = AlmacenDocumentosDisco(tmp_path)
    almacen.guardar("req/documento.pdf", b"%PDF-1")
    assert almacen.leer("req/documento.pdf") == b"%PDF-1"
    # No quedan archivos temporales.
    assert [p.name for p in (tmp_path / "req").iterdir()] == ["documento.pdf"]


def test_nunca_sobrescribe(tmp_path):
    almacen = AlmacenDocumentosDisco(tmp_path)
    almacen.guardar("a.pdf", b"original")
    with pytest.raises(DocumentoExistente):
        almacen.guardar("a.pdf", b"otro")
    assert almacen.leer("a.pdf") == b"original"


@pytest.mark.parametrize(
    "clave", ["../fuera.pdf", "/abs.pdf", "a/../../b.pdf", "", "a\\b.pdf", "a//b", "./a.pdf"]
)
def test_rechaza_claves_fuera_de_la_carpeta(tmp_path, clave):
    with pytest.raises(ValueError):
        AlmacenDocumentosDisco(tmp_path).guardar(clave, b"x")


def test_leer_lo_que_no_existe(tmp_path):
    with pytest.raises(DocumentoNoEncontrado):
        AlmacenDocumentosDisco(tmp_path).leer("no-existe.pdf")


def test_no_tiene_metodo_para_borrar():
    nombres = [n.lower() for n in dir(AlmacenDocumentosDisco) if not n.startswith("_")]
    assert nombres == ["guardar", "leer"]
