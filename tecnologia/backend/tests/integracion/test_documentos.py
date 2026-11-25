"""Incremento 002: documento oficial, revisión antes de firmar y PDF (US1 a US4).

La verificación de un PDF subido (US5, EQ-02) está en ``test_eq02_pdf.py``.
"""

from pathlib import Path

import pytest
from sqlalchemy import text

from tests.integracion.apoyo import (
    URL,
    avanzar,
    crear_en_transito,
    crear_enviada,
    firmar,
    firmar_acta,
)

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


# --- US2: revisión antes de firmar (T021) ---


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"decision": "APROBAR"},
        {"decision": "APROBAR", "documento_revisado": False},
        {"decision": "RECHAZAR", "motivo": "No corresponde"},
    ],
    ids=["sin-campo", "false", "rechazo-sin-campo"],
)
def test_firmar_sin_revisar_el_documento_es_422_y_no_registra_nada(cliente, login, cuerpo):
    rid = crear_enviada(cliente, login)
    cabeceras = login("cmdte.bim11")
    respuesta = cliente.post(f"{URL}/{rid}/firmas", json=cuerpo, headers=cabeceras)
    assert respuesta.status_code == 422, respuesta.text
    assert "documento_revisado" in respuesta.text
    assert cliente.get(f"{URL}/{rid}/firmas", headers=cabeceras).json() == []
    detalle = cliente.get(f"{URL}/{rid}", headers=cabeceras).json()
    assert detalle["estado"] == "PENDIENTE_VB_UNIDAD"


def test_firmar_con_el_documento_revisado(cliente, login):
    rid = crear_enviada(cliente, login)
    respuesta = cliente.post(
        f"{URL}/{rid}/firmas",
        json={"decision": "APROBAR", "documento_revisado": True},
        headers=login("cmdte.bim11"),
    )
    assert respuesta.status_code == 201, respuesta.text


# --- US3: descargar el PDF con código de verificación (T028) ---


def _pdf(cliente, cabeceras, rid, ruta="documento.pdf"):
    return cliente.get(f"{URL}/{rid}/{ruta}", headers=cabeceras)


def test_descargar_pdf_dos_veces_devuelve_los_mismos_bytes(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    oficial = login("oficial.bim11")
    primera = _pdf(cliente, oficial, rid)
    assert primera.status_code == 200, primera.text
    assert primera.headers["content-type"] == "application/pdf"
    assert primera.content.startswith(b"%PDF-")
    assert "attachment" in primera.headers["content-disposition"]
    codigo = primera.headers["x-codigo-verificacion"]
    assert codigo.startswith("SGA-") and codigo.encode() in primera.content
    # Otro usuario autorizado (el comandante) recibe el mismo PDF ya emitido.
    segunda = _pdf(cliente, login("cmdte.bim11"), rid)
    assert segunda.content == primera.content
    assert segunda.headers["x-codigo-verificacion"] == codigo


def test_una_firma_nueva_emite_otro_pdf_y_conserva_el_anterior(cliente, login, motor):
    from app.core.config import obtener_configuracion
    from app.modules.signing.infraestructura.almacen_documentos_disco import (
        AlmacenDocumentosDisco,
    )

    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    oficial = login("oficial.bim11")
    primero = _pdf(cliente, oficial, rid)
    avanzar_desde = firmar(cliente, login, rid, "jlog.1de")
    assert avanzar_desde.status_code == 201
    segundo = _pdf(cliente, oficial, rid)
    assert segundo.headers["x-codigo-verificacion"] != primero.headers["x-codigo-verificacion"]
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT codigo_verificacion, clave_almacen, huella_sha256 FROM documento_emitido "
                "WHERE requerimiento_id = :r ORDER BY emitido_en"
            ),
            {"r": rid},
        ).all()
    assert [f.codigo_verificacion for f in filas] == [
        primero.headers["x-codigo-verificacion"],
        segundo.headers["x-codigo-verificacion"],
    ]
    # El PDF anterior sigue en el almacenamiento, sin cambios.
    almacen = AlmacenDocumentosDisco(obtener_configuracion().documentos_dir)
    assert almacen.leer(filas[0].clave_almacen) == primero.content


def test_pdf_sin_firmas_es_409(cliente, login):
    rid = crear_enviada(cliente, login)
    respuesta = _pdf(cliente, login("oficial.bim11"), rid)
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "SIN_FIRMAS"


def test_pdf_ajeno_404_y_sin_sesion_401(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    assert _pdf(cliente, login("oficial.bim21"), rid).status_code == 404
    assert cliente.get(f"{URL}/{rid}/documento.pdf").status_code == 401


def test_pdf_guardado_que_no_coincide_con_su_huella_no_se_entrega(cliente, login, motor):
    from app.core.config import obtener_configuracion

    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    oficial = login("oficial.bim11")
    assert _pdf(cliente, oficial, rid).status_code == 200
    with motor.connect() as conexion:
        clave = conexion.scalar(
            text("SELECT clave_almacen FROM documento_emitido WHERE requerimiento_id = :r"),
            {"r": rid},
        )
    ruta = Path(obtener_configuracion().documentos_dir) / clave
    ruta.write_bytes(ruta.read_bytes() + b"%alterado")
    respuesta = _pdf(cliente, oficial, rid)
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "DOCUMENTO_INCONSISTENTE"


# --- US4: documento y PDF del acta de recepción (T032) ---


def _recibida_con_diferencia(cliente, login) -> str:
    rid = crear_en_transito(cliente, login)
    respuesta = firmar_acta(
        cliente,
        login,
        rid,
        {"INT-001": 8, "INT-002": 5},
        observaciones={"INT-001": "Llegaron 2 raciones dañadas"},
    )
    assert respuesta.status_code == 201, respuesta.text
    return rid


def test_documento_del_acta_con_lineas_diferencias_y_sello(cliente, login):
    rid = _recibida_con_diferencia(cliente, login)
    respuesta = cliente.get(f"{URL}/{rid}/acta/documento", headers=login("oficial.bim11"))
    assert respuesta.status_code == 200, respuesta.text
    doc = respuesta.json()
    assert doc["tipo"] == "ACTA"
    assert doc["tiene_diferencias"] is True
    lineas = {i["codigo"]: i for i in doc["items"]}
    assert (lineas["INT-001"]["cantidad_despachada"], lineas["INT-001"]["cantidad_recibida"]) == (
        10,
        8,
    )
    assert lineas["INT-001"]["observacion"] == "Llegaron 2 raciones dañadas"
    assert lineas["INT-002"]["cantidad_recibida"] == 5
    assert [s["nivel"] for s in doc["sellos"]] == ["ACTA_RECEPCION"]
    assert doc["pdf_disponible"] is True


def test_pdf_del_acta_tiene_su_propio_codigo_y_no_cambia_el_del_requerimiento(cliente, login):
    rid = crear_en_transito(cliente, login)
    oficial = login("oficial.bim11")
    pdf_req = _pdf(cliente, oficial, rid)
    assert pdf_req.status_code == 200
    assert firmar_acta(cliente, login, rid, {"INT-001": 10, "INT-002": 5}).status_code == 201
    pdf_acta = _pdf(cliente, oficial, rid, "acta/documento.pdf")
    assert pdf_acta.status_code == 200, pdf_acta.text
    assert pdf_acta.headers["content-type"] == "application/pdf"
    assert "-acta.pdf" in pdf_acta.headers["content-disposition"]
    codigo_acta = pdf_acta.headers["x-codigo-verificacion"]
    assert codigo_acta != pdf_req.headers["x-codigo-verificacion"]
    # Firmar el acta no cambia el PDF del requerimiento.
    de_nuevo = _pdf(cliente, oficial, rid)
    assert de_nuevo.content == pdf_req.content
    assert _pdf(cliente, oficial, rid, "acta/documento.pdf").content == pdf_acta.content


def test_acta_inexistente_404_y_ajena_404(cliente, login):
    rid = crear_en_transito(cliente, login)
    oficial = login("oficial.bim11")
    assert cliente.get(f"{URL}/{rid}/acta/documento", headers=oficial).status_code == 404
    assert _pdf(cliente, oficial, rid, "acta/documento.pdf").status_code == 404
    rid2 = _recibida_con_diferencia(cliente, login)
    ajeno = login("oficial.bim21")
    assert cliente.get(f"{URL}/{rid2}/acta/documento", headers=ajeno).status_code == 404
    assert _pdf(cliente, ajeno, rid2, "acta/documento.pdf").status_code == 404
    assert cliente.get(f"{URL}/{rid2}/acta/documento.pdf").status_code == 401
