"""Incremento 002: documento oficial, revisión antes de firmar y PDF (US1 a US4).

La verificación de un PDF subido (US5, EQ-02) está en ``test_eq02_pdf.py``.
"""

import pytest
from sqlalchemy import text

from tests.integracion.apoyo import URL, avanzar, crear_enviada, firmar

# --- US1: documento oficial (T015) ---


def test_documento_con_encabezado_items_y_sellos_en_orden(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 2)
    respuesta = cliente.get(f"{URL}/{rid}/documento", headers=login("oficial.bim11"))
    assert respuesta.status_code == 200, respuesta.text
    doc = respuesta.json()
    assert doc["tipo"] == "REQUERIMIENTO"
    assert doc["codigo"].startswith("REQ-")
    assert doc["unidad"]["codigo"] == "BIM-11"
    assert doc["gran_unidad"]["codigo"] == "1DE"
    assert doc["almacen"]["codigo"]
    assert doc["fecha"]
    assert [i["codigo"] for i in doc["items"]] == ["INT-001", "INT-002"]
    assert [i["cantidad_solicitada"] for i in doc["items"]] == [10, 5]
    assert [s["nivel"] for s in doc["sellos"]] == ["VB_UNIDAD", "CONFORMIDAD_GU"]
    sello = doc["sellos"][0]
    assert sello["decision"] == "APROBAR"
    assert sello["rol"] == "COMANDANTE_UNIDAD"
    assert sello["organo"]["codigo"] == "BIM-11"
    assert sello["metodo"] == "ed25519-sha256-v1"
    assert len(sello["huella_sha256"]) == 64
    assert sello["firmante"]
    assert len(doc["huella_contenido"]) == 64
    assert doc["pdf_disponible"] is True


def test_documento_de_un_rechazo_muestra_el_motivo(cliente, login):
    rid = crear_enviada(cliente, login)
    respuesta = firmar(
        cliente, login, rid, "cmdte.bim11", decision="RECHAZAR", motivo="No corresponde"
    )
    assert respuesta.status_code == 201, respuesta.text
    doc = cliente.get(f"{URL}/{rid}/documento", headers=login("oficial.bim11")).json()
    assert [(s["decision"], s["motivo"]) for s in doc["sellos"]] == [("RECHAZAR", "No corresponde")]


def test_documento_sin_firmas(cliente, login):
    rid = crear_enviada(cliente, login)
    doc = cliente.get(f"{URL}/{rid}/documento", headers=login("oficial.bim11")).json()
    assert doc["sellos"] == []
    assert doc["pdf_disponible"] is False


@pytest.mark.parametrize("ruta", ["documento"])
def test_documento_ajeno_404_y_sin_sesion_401(cliente, login, ruta):
    rid = crear_enviada(cliente, login)
    assert cliente.get(f"{URL}/{rid}/{ruta}", headers=login("oficial.bim21")).status_code == 404
    assert cliente.get(f"{URL}/{rid}/{ruta}").status_code == 401


def test_documento_emitido_es_inmutable(motor):
    """El disparador de 0003 rechaza UPDATE y DELETE en documento_emitido (FR-011)."""
    with motor.connect() as conexion:
        disparadores = conexion.scalar(
            text("SELECT count(*) FROM pg_trigger WHERE tgname = 'tg_documento_emitido_inmutable'")
        )
    assert disparadores == 1
