"""T085 — US6: anular con justificación (escenarios 1 a 4 de spec.md; FR-022)."""

import pytest
from sqlalchemy import text

from tests.integracion.apoyo import (
    INTENDENCIA,
    URL,
    avanzar,
    crear_en_transito,
    crear_enviada,
    firmar,
    firmar_acta,
    historial,
)

MOTIVO = "Material de guerra bloqueado hasta el COLOGE"


def crear_borrador(cliente, login, datos: dict = INTENDENCIA) -> str:
    creado = cliente.post(URL, json=datos, headers=login("oficial.bim11"))
    assert creado.status_code == 201, creado.text
    return creado.json()["id"]


def anular(cliente, login, rid: str, motivo=MOTIVO, usuario: str = "oficial.bim11"):
    cuerpo = {} if motivo is None else {"motivo": motivo}
    return cliente.post(f"{URL}/{rid}/anular", json=cuerpo, headers=login(usuario))


# --- Escenario 1: anular desde BORRADOR con motivo ---


def test_anular_desde_borrador_con_motivo(cliente, login, motor):
    rid = crear_borrador(cliente, login)
    respuesta = anular(cliente, login, rid)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "ANULADA"
    assert respuesta.json()["acciones_disponibles"] == []

    ultimo = historial(motor, rid)[-1]
    assert (ultimo["accion"], ultimo["estado_anterior"], ultimo["estado_nuevo"]) == (
        "ANULAR",
        "BORRADOR",
        "ANULADA",
    )
    assert ultimo["motivo"] == MOTIVO
    # No se borra: sigue en la bandeja de la unidad y su línea de tiempo.
    bandeja = cliente.get(URL, params={"estado": "ANULADA"}, headers=login("oficial.bim11")).json()
    assert [r["id"] for r in bandeja["items"]] == [rid]
    linea = cliente.get(f"{URL}/{rid}/historial", headers=login("oficial.bim11")).json()
    assert linea[-1]["motivo"] == MOTIVO
    with motor.connect() as conexion:
        eventos = list(
            conexion.scalars(
                text(
                    "SELECT tipo_evento FROM registro_auditoria WHERE entidad_id = :id ORDER BY id"
                ),
                {"id": rid},
            )
        )
    assert eventos[-1] == "REQUERIMIENTO.ANULAR"


def test_anular_el_material_de_guerra_bloqueado(cliente, login):
    from tests.integracion.apoyo import cuerpo

    rid = crear_borrador(cliente, login, cuerpo(("MG-001", 2)))
    bloqueado = cliente.post(f"{URL}/{rid}/enviar", headers=login("oficial.bim11"))
    assert bloqueado.json()["codigo"] == "REQUIERE_COLOGE"
    assert anular(cliente, login, rid).json()["estado"] == "ANULADA"


def test_una_anulada_no_admite_mas_acciones(cliente, login, motor):
    rid = crear_borrador(cliente, login)
    anular(cliente, login, rid)
    oficial = login("oficial.bim11")
    assert cliente.post(f"{URL}/{rid}/enviar", headers=oficial).status_code == 409
    assert cliente.put(f"{URL}/{rid}", json=INTENDENCIA, headers=oficial).status_code == 409
    assert anular(cliente, login, rid).status_code == 409
    # La base de datos tampoco deja modificarla (estado final).
    with pytest.raises(Exception, match="(?i)inmutable"), motor.begin() as conexion:
        conexion.execute(
            text("UPDATE requerimiento SET estado = 'BORRADOR' WHERE id = :id"), {"id": rid}
        )


# --- Escenario 2: sin motivo ---


@pytest.mark.parametrize(
    "motivo", [None, "", "   ", "abc"], ids=["sin", "vacio", "blancos", "corto"]
)
def test_anular_sin_motivo_responde_422(cliente, login, motivo):
    rid = crear_borrador(cliente, login)
    respuesta = anular(cliente, login, rid, motivo)
    assert respuesta.status_code == 422
    assert "motivo" in [d["campo"] for d in respuesta.json()["detalles"]]
    detalle = cliente.get(f"{URL}/{rid}", headers=login("oficial.bim11")).json()
    assert detalle["estado"] == "BORRADOR"


def test_motivo_de_solo_espacios_largo_responde_422(cliente, login):
    rid = crear_borrador(cliente, login)
    assert anular(cliente, login, rid, " " * 10).status_code == 422


# --- Escenario 3: desde cualquier otro estado ---


def _en_estado(cliente, login, estado: str) -> str:
    if estado == "RECHAZADA":
        rid = crear_enviada(cliente, login)
        firmar(cliente, login, rid, "cmdte.bim11", "RECHAZAR", "No corresponde")
        return rid
    if estado == "EN_TRANSITO":
        return crear_en_transito(cliente, login)
    if estado == "CONFIRMADA":
        rid = crear_en_transito(cliente, login)
        firmar_acta(cliente, login, rid, {"INT-001": 10, "INT-002": 5})
        return rid
    niveles = {
        "PENDIENTE_VB_UNIDAD": 0,
        "PENDIENTE_CONFORMIDAD": 1,
        "PENDIENTE_APROBACION": 2,
        "APROBADA": 3,
    }[estado]
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, niveles)
    return rid


@pytest.mark.parametrize(
    "estado",
    [
        "PENDIENTE_VB_UNIDAD",
        "PENDIENTE_CONFORMIDAD",
        "PENDIENTE_APROBACION",
        "APROBADA",
        "EN_TRANSITO",
        "CONFIRMADA",
        "RECHAZADA",
    ],
)
def test_anular_fuera_de_borrador_responde_409(cliente, login, motor, estado):
    rid = _en_estado(cliente, login, estado)
    antes = historial(motor, rid)
    respuesta = anular(cliente, login, rid)
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["codigo"] == "TRANSICION_NO_PERMITIDA"
    detalle = cliente.get(f"{URL}/{rid}", headers=login("oficial.bim11")).json()
    assert detalle["estado"] == estado
    assert historial(motor, rid) == antes


# --- Escenario 4: otra unidad u otro rol ---


def test_otra_unidad_recibe_404(cliente, login):
    rid = crear_borrador(cliente, login)
    for usuario in ("oficial.bim12", "oficial.bim21"):
        assert anular(cliente, login, rid, usuario=usuario).status_code == 404, usuario


@pytest.mark.parametrize(
    "usuario", ["cmdte.bim11", "jlog.1de", "jalm.sinte", "almacenero.sinte", "auditor"]
)
def test_otro_rol_recibe_403(cliente, login, usuario):
    rid = crear_borrador(cliente, login)
    respuesta = anular(cliente, login, rid, usuario=usuario)
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "SIN_PERMISO"


def test_sin_sesion_responde_401(cliente, login):
    rid = crear_borrador(cliente, login)
    assert cliente.post(f"{URL}/{rid}/anular", json={"motivo": MOTIVO}).status_code == 401
