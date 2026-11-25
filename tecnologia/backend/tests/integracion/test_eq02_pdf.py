"""T038 — US5 y EQ-02 con el PDF: verificar un PDF subido contra la API y PostgreSQL reales.

AUTENTICO solo si el archivo es el emitido, sin cambios, y las firmas que contiene siguen íntegras
con los datos actuales de la base de datos. Cualquier alteración (un byte del archivo o una
cantidad firmada en la BD) da ALTERADO.
"""

import pytest

from tests.integracion.apoyo import URL, avanzar, crear_enviada
from tests.integracion.test_eq02_integridad import alterar

VERIFICACION = "/api/v1/documentos/verificacion"
PDF = {"Content-Type": "application/pdf"}


def _pdf_emitido(cliente, login) -> tuple[str, bytes, str]:
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 2)
    respuesta = cliente.get(f"{URL}/{rid}/documento.pdf", headers=login("oficial.bim11"))
    assert respuesta.status_code == 200, respuesta.text
    return rid, respuesta.content, respuesta.headers["x-codigo-verificacion"]


def _verificar(cliente, cabeceras, contenido: bytes):
    return cliente.post(VERIFICACION, content=contenido, headers={**cabeceras, **PDF})


def test_pdf_tal_cual_es_autentico(cliente, login):
    rid, contenido, codigo = _pdf_emitido(cliente, login)
    respuesta = _verificar(cliente, login("oficial.bim11"), contenido)
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["resultado"] == "AUTENTICO"
    assert cuerpo["motivo"]
    doc = cuerpo["documento"]
    assert doc["codigo_verificacion"] == codigo
    assert doc["tipo"] == "REQUERIMIENTO"
    assert doc["requerimiento_id"] == rid
    assert doc["requerimiento_codigo"].startswith("REQ-")
    assert doc["emitido_en"]
    assert [s["nivel"] for s in doc["sellos"]] == ["VB_UNIDAD", "CONFORMIDAD_GU"]


def test_un_byte_cambiado_es_alterado(cliente, login):
    _, contenido, _ = _pdf_emitido(cliente, login)
    alterado = bytearray(contenido)
    alterado[len(alterado) // 2] ^= 0x01
    cuerpo = _verificar(cliente, login("oficial.bim11"), bytes(alterado)).json()
    assert cuerpo["resultado"] == "ALTERADO"
    assert "modificado" in cuerpo["motivo"]


def test_eq02_cantidad_firmada_cambiada_en_la_bd_es_alterado(cliente, login, motor):
    rid, contenido, _ = _pdf_emitido(cliente, login)
    alterar(
        motor,
        "item_requerimiento",
        "tg_item_requerimiento_protegido",
        "UPDATE item_requerimiento SET cantidad_solicitada = cantidad_solicitada + 1 "
        "WHERE requerimiento_id = :id AND item_id = (SELECT id FROM item WHERE codigo = 'INT-002')",
        {"id": rid},
    )
    cuerpo = _verificar(cliente, login("oficial.bim11"), contenido).json()
    assert cuerpo["resultado"] == "ALTERADO"
    assert "alterados" in cuerpo["motivo"]


def test_pdf_ajeno_es_404_y_sin_sesion_401(cliente, login):
    _, contenido, _ = _pdf_emitido(cliente, login)
    assert _verificar(cliente, login("oficial.bim21"), contenido).status_code == 404
    assert cliente.post(VERIFICACION, content=contenido, headers=PDF).status_code == 401


def test_pdf_sin_codigo_es_alterado(cliente, login):
    cuerpo = _verificar(cliente, login("oficial.bim11"), b"%PDF-1.4 cualquier cosa %%EOF").json()
    assert cuerpo["resultado"] == "ALTERADO"
    assert cuerpo["documento"] is None


@pytest.mark.parametrize(
    "contenido",
    [b"", b"no soy un pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024)],
    ids=["vacio", "no-pdf", "mas-de-5MB"],
)
def test_archivo_invalido_es_422(cliente, login, contenido):
    respuesta = _verificar(cliente, login("oficial.bim11"), contenido)
    assert respuesta.status_code == 422, respuesta.text
