"""T074 — US4: firmar el acta de recepción y verificar su integridad (escenarios 1 a 4 y 6 de
spec.md; FR-021, FR-023 a FR-025) contra la API y PostgreSQL reales."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.integracion.apoyo import (
    URL,
    avanzar,
    crear_en_transito,
    crear_enviada,
    firmar_acta,
    historial,
)

COMPLETO = {"INT-001": 10, "INT-002": 5}


# --- Escenario 1: el acta registra lo recibido y las diferencias ---


def test_acta_sin_diferencias(cliente, login, motor):
    rid = crear_en_transito(cliente, login)
    respuesta = firmar_acta(cliente, login, rid, COMPLETO)
    assert respuesta.status_code == 201, respuesta.text
    acta = respuesta.json()
    assert acta["requerimiento_id"] == rid
    assert acta["tiene_diferencias"] is False
    assert acta["firma"]["nivel"] == "ACTA_RECEPCION"
    assert acta["firma"]["firmante"] == "Oficial de logística BIM-11"
    assert acta["firma"]["organo"]["codigo"] == "BIM-11"
    assert acta["firma"]["firmado_en"]
    assert {i["item"]["codigo"]: i["cantidad_recibida"] for i in acta["items"]} == COMPLETO

    detalle = cliente.get(f"{URL}/{rid}", headers=login("oficial.bim11")).json()
    assert detalle["estado"] == "CONFIRMADA"
    assert detalle["acciones_disponibles"] == []
    ultimo = historial(motor, rid)[-1]
    assert (ultimo["accion"], ultimo["estado_anterior"], ultimo["estado_nuevo"]) == (
        "FIRMAR_ACTA",
        "EN_TRANSITO",
        "CONFIRMADA",
    )


def test_acta_con_diferencias_y_observaciones(cliente, login):
    rid = crear_en_transito(cliente, login)
    respuesta = firmar_acta(
        cliente,
        login,
        rid,
        {"INT-001": 8, "INT-002": 5},
        observaciones={"INT-001": "  Llegaron 2 raciones dañadas  "},
    )
    assert respuesta.status_code == 201, respuesta.text
    acta = respuesta.json()
    assert acta["tiene_diferencias"] is True
    racion = next(i for i in acta["items"] if i["item"]["codigo"] == "INT-001")
    assert (racion["cantidad_despachada"], racion["cantidad_recibida"]) == (10, 8)
    assert racion["observacion"] == "Llegaron 2 raciones dañadas"
    # El acta se puede consultar después, también por el auditor.
    consultada = cliente.get(f"{URL}/{rid}/acta", headers=login("auditor"))
    assert consultada.status_code == 200
    assert consultada.json()["id"] == acta["id"]


def test_acta_inexistente_responde_404(cliente, login):
    rid = crear_en_transito(cliente, login)
    respuesta = cliente.get(f"{URL}/{rid}/acta", headers=login("oficial.bim11"))
    assert respuesta.status_code == 404


# --- Escenario 2: otra unidad u otro rol ---


def test_otra_unidad_recibe_404_y_otro_rol_403(cliente, login, motor):
    rid = crear_en_transito(cliente, login)
    assert firmar_acta(cliente, login, rid, COMPLETO, "oficial.bim12").status_code == 404
    for usuario in ("cmdte.bim11", "jlog.1de", "jalm.sinte", "almacenero.sinte", "auditor"):
        assert firmar_acta(cliente, login, rid, COMPLETO, usuario).status_code == 403, usuario
    detalle = cliente.get(f"{URL}/{rid}", headers=login("oficial.bim11")).json()
    assert detalle["estado"] == "EN_TRANSITO"
    with motor.connect() as conexion:
        assert conexion.scalar(text("SELECT count(*) FROM acta_recepcion")) == 0


# --- Escenario 3: el acta es inmutable ---


def test_volver_a_firmar_el_acta_responde_409(cliente, login, motor):
    rid = crear_en_transito(cliente, login)
    assert firmar_acta(cliente, login, rid, COMPLETO).status_code == 201
    respuesta = firmar_acta(cliente, login, rid, {"INT-001": 1, "INT-002": 1})
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "NIVEL_YA_FIRMADO"
    with motor.connect() as conexion:
        assert conexion.scalar(text("SELECT count(*) FROM acta_recepcion")) == 1
        recibido = conexion.scalar(
            text(
                "SELECT sum(cantidad_recibida) FROM item_requerimiento WHERE requerimiento_id = :id"
            ),
            {"id": rid},
        )
    assert recibido == 15


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE acta_recepcion SET tiene_diferencias = NOT tiene_diferencias",
        "DELETE FROM acta_recepcion",
        "UPDATE firma SET huella_sha256 = repeat('0', 64)",
        "UPDATE item_requerimiento SET cantidad_recibida = 0",
        "UPDATE requerimiento SET estado = 'EN_TRANSITO'",
        "DELETE FROM historial_requerimiento",
    ],
    ids=["acta", "borrar-acta", "firma", "items", "estado", "historial"],
)
def test_la_base_de_datos_rechaza_modificar_el_acta(cliente, login, motor, sentencia):
    rid = crear_en_transito(cliente, login)
    assert firmar_acta(cliente, login, rid, COMPLETO).status_code == 201
    with pytest.raises(DBAPIError, match="(?i)inmutable|no se puede|final"), motor.begin() as c:
        c.execute(text(sentencia))


# --- Escenario 6: solo se firma lo que está EN_TRANSITO ---


def test_firmar_el_acta_fuera_de_en_transito_responde_409(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 3)  # APROBADA, sin despachar
    respuesta = firmar_acta(cliente, login, rid, COMPLETO)
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TRANSICION_NO_PERMITIDA"


@pytest.mark.parametrize(
    ("recibido", "campo"),
    [
        ({"INT-001": 10}, "faltan ítems"),
        ({"INT-001": 10, "INT-002": 5, "INT-003": 1}, "ítem ajeno"),
        ({"INT-001": -1, "INT-002": 5}, "negativa"),
    ],
)
def test_acta_con_datos_invalidos_responde_422(cliente, login, recibido, campo):
    rid = crear_en_transito(cliente, login)
    assert firmar_acta(cliente, login, rid, recibido).status_code == 422, campo


def test_observacion_demasiado_larga_responde_422(cliente, login):
    rid = crear_en_transito(cliente, login)
    respuesta = firmar_acta(cliente, login, rid, COMPLETO, observaciones={"INT-001": "x" * 501})
    assert respuesta.status_code == 422


# --- Escenario 4: verificación INTEGRA con firmante y fecha ---


def test_la_verificacion_responde_integra_con_firmante_y_fecha(cliente, login):
    rid = crear_en_transito(cliente, login)
    firmar_acta(cliente, login, rid, {"INT-001": 9, "INT-002": 5})
    for usuario in ("oficial.bim11", "auditor", "jalm.sinte"):
        respuesta = cliente.get(f"{URL}/{rid}/verificacion", headers=login(usuario))
        assert respuesta.status_code == 200, usuario
        verificacion = respuesta.json()
        assert verificacion["resultado"] == "INTEGRA"
        assert [f["nivel"] for f in verificacion["firmas"]] == [
            "VB_UNIDAD",
            "CONFORMIDAD_GU",
            "APROBACION_ALMACEN",
            "ACTA_RECEPCION",
        ]
        assert all(f["resultado"] == "INTEGRA" for f in verificacion["firmas"])
        acta = verificacion["firmas"][-1]
        assert acta["firmante"] == "Oficial de logística BIM-11"
        assert acta["firmado_en"]


def test_la_verificacion_respeta_la_jurisdiccion(cliente, login):
    rid = crear_en_transito(cliente, login)
    firmar_acta(cliente, login, rid, COMPLETO)
    assert cliente.get(f"{URL}/{rid}/verificacion", headers=login("jlog.2de")).status_code == 404
    assert cliente.get(f"{URL}/{rid}/acta", headers=login("oficial.bim21")).status_code == 404
    assert cliente.get(f"{URL}/{rid}/verificacion").status_code == 401
