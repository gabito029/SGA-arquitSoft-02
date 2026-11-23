"""T042 — US1: registrar y enviar una solicitud (escenarios 1 a 6 de spec.md; FR-005 a FR-008,
FR-012, FR-029) contra la API y PostgreSQL reales."""

import re
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.core.config import obtener_configuracion
from seeds.cargar import id_fijo

URL = "/api/v1/requerimientos"


def item(codigo: str) -> str:
    return str(id_fijo("item", codigo))


def cuerpo(*lineas: tuple[str, int]) -> dict:
    return {"items": [{"item_id": item(c), "cantidad": n} for c, n in lineas]}


INTENDENCIA = cuerpo(("INT-001", 10), ("INT-002", 5))  # 355.00 + 900.00 = 1 255.00
MATERIAL_GUERRA = cuerpo(("MG-001", 2))


@pytest.fixture
def oficial(login):
    return login("oficial.bim11")


@pytest.fixture
def crear(cliente, oficial):
    def _crear(datos: dict = INTENDENCIA, cabeceras: dict | None = None) -> dict:
        respuesta = cliente.post(URL, json=datos, headers=cabeceras or oficial)
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


def historial(motor, requerimiento_id: str) -> list[dict]:
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT h.accion, h.estado_anterior, h.estado_nuevo, u.usuario, h.rol, "
                "o.codigo AS organo, h.motivo, h.ocurrido_en "
                "FROM historial_requerimiento h JOIN usuario u ON u.id = h.usuario_id "
                "JOIN organo o ON o.id = h.organo_id "
                "WHERE h.requerimiento_id = :id ORDER BY h.id"
            ),
            {"id": requerimiento_id},
        )
        return [dict(f._mapping) for f in filas]


def eventos_auditoria(motor, requerimiento_id: str) -> list[str]:
    with motor.connect() as conexion:
        return list(
            conexion.scalars(
                text(
                    "SELECT tipo_evento FROM registro_auditoria WHERE entidad_id = :id ORDER BY id"
                ),
                {"id": requerimiento_id},
            )
        )


# --- Escenario 1: crear y enviar ---


def test_crear_y_enviar_intendencia(cliente, oficial, crear, motor):
    creado = crear()
    assert creado["estado"] == "BORRADOR"
    assert re.fullmatch(r"REQ-\d{4}-\d{6}", creado["codigo"])
    assert creado["categoria"] == "INTENDENCIA"
    assert creado["unidad"]["codigo"] == "BIM-11"
    assert creado["gran_unidad"]["codigo"] == "1DE"
    assert creado["almacen"]["codigo"] == "SINTE"
    assert len(creado["items"]) == 2
    assert creado["acciones_disponibles"] == ["EDITAR", "ENVIAR", "ANULAR"]

    respuesta = cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    assert respuesta.status_code == 200, respuesta.text
    enviado = respuesta.json()
    assert enviado["estado"] == "PENDIENTE_VB_UNIDAD"
    assert enviado["monto_total"] == "1255.00"
    assert enviado["acciones_disponibles"] == []  # ya no es editable (FR-008)

    pasos = historial(motor, creado["id"])
    assert [(p["accion"], p["estado_anterior"], p["estado_nuevo"]) for p in pasos] == [
        ("CREAR", None, "BORRADOR"),
        ("ENVIAR", "BORRADOR", "PENDIENTE_VB_UNIDAD"),
    ]
    assert all(p["usuario"] == "oficial.bim11" and p["organo"] == "BIM-11" for p in pasos)
    assert all(p["rol"] == "OFICIAL_LOGISTICA" and p["ocurrido_en"] for p in pasos)
    assert eventos_auditoria(motor, creado["id"]) == [
        "REQUERIMIENTO.CREAR",
        "REQUERIMIENTO.ENVIAR",
    ]


def test_el_comandante_ve_la_enviada_con_firmar_y_rechazar(cliente, oficial, crear, login):
    creado = crear()
    cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    respuesta = cliente.get(f"{URL}/{creado['id']}", headers=login("cmdte.bim11"))
    assert respuesta.status_code == 200
    assert respuesta.json()["acciones_disponibles"] == ["FIRMAR", "RECHAZAR"]


# --- Escenario 2: guardar en BORRADOR, solo lo ve su unidad ---


def test_guardar_en_borrador_solo_lo_ven_los_oficiales_de_su_unidad(cliente, oficial, crear, login):
    creado = crear()
    assert cliente.get(f"{URL}/{creado['id']}", headers=oficial).status_code == 200
    for ajeno in ("oficial.bim12", "cmdte.bim11", "jlog.1de", "jalm.sinte", "auditor"):
        respuesta = cliente.get(f"{URL}/{creado['id']}", headers=login(ajeno))
        assert respuesta.status_code == 404, ajeno
        assert respuesta.json()["codigo"] == "NO_ENCONTRADO"


# --- Escenario 3: validaciones con campo y motivo (422) ---


@pytest.mark.parametrize(
    ("datos", "campo"),
    [
        ({"items": []}, "items"),
        ({}, "items"),
        (cuerpo(("INT-001", 0)), "items.0.cantidad"),
        (cuerpo(("INT-001", -3)), "items.0.cantidad"),
        ({"items": [{"item_id": item("INT-001"), "cantidad": 1.5}]}, "items.0.cantidad"),
        (cuerpo(("INT-001", 1), ("INT-001", 2)), "items"),
        ({"items": [{"item_id": "no-es-uuid", "cantidad": 1}]}, "items.0.item_id"),
    ],
    ids=["sin-items", "sin-campo-items", "cantidad-cero", "negativa", "decimal", "repetido", "id"],
)
def test_datos_invalidos_responden_422_con_el_campo(cliente, oficial, datos, campo, motor):
    respuesta = cliente.post(URL, json=datos, headers=oficial)
    assert respuesta.status_code == 422, respuesta.text
    error = respuesta.json()
    assert error["codigo"] == "VALIDACION"
    assert campo in [d["campo"] for d in error["detalles"]]
    assert all(d["mensaje"] for d in error["detalles"])
    with motor.connect() as conexion:
        assert conexion.scalar(text("SELECT count(*) FROM requerimiento")) == 0


def test_el_item_repetido_explica_el_motivo(cliente, oficial):
    respuesta = cliente.post(URL, json=cuerpo(("INT-001", 1), ("INT-001", 2)), headers=oficial)
    assert respuesta.json()["detalles"][0]["mensaje"] == "La solicitud no puede repetir un ítem."


def test_item_inexistente_responde_422(cliente, oficial):
    datos = {"items": [{"item_id": "00000000-0000-0000-0000-000000000000", "cantidad": 1}]}
    respuesta = cliente.post(URL, json=datos, headers=oficial)
    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == "items.0.item_id"


def test_item_inactivo_responde_422(cliente, oficial, motor):
    with motor.begin() as conexion:
        conexion.execute(text("UPDATE item SET activo = false WHERE codigo = 'INT-003'"))
    respuesta = cliente.post(URL, json=cuerpo(("INT-001", 1), ("INT-003", 1)), headers=oficial)
    assert respuesta.status_code == 422
    detalle = respuesta.json()["detalles"][0]
    assert detalle["campo"] == "items.1.item_id"
    assert "inactivo" in detalle["mensaje"]


def test_mezclar_categorias_responde_422(cliente, oficial):
    respuesta = cliente.post(URL, json=cuerpo(("INT-001", 1), ("MG-001", 1)), headers=oficial)
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "ITEMS_INVALIDOS"


# --- Escenario 4: otro rol (403) y sin sesión (401) ---


@pytest.mark.parametrize("usuario", ["almacenero.sinte", "cmdte.bim11", "jlog.1de", "auditor"])
def test_otro_rol_no_puede_registrar(cliente, login, usuario):
    respuesta = cliente.post(URL, json=INTENDENCIA, headers=login(usuario))
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "SIN_PERMISO"


def test_otro_rol_no_puede_enviar(cliente, crear, login):
    creado = crear()
    respuesta = cliente.post(f"{URL}/{creado['id']}/enviar", headers=login("cmdte.bim11"))
    assert respuesta.status_code == 403


def test_sin_sesion_responde_401(cliente):
    assert cliente.post(URL, json=INTENDENCIA).status_code == 401
    assert cliente.get(URL).status_code == 401


def test_otra_unidad_no_puede_enviar_ni_editar(cliente, crear, login):
    creado = crear()
    ajeno = login("oficial.bim21")
    assert cliente.post(f"{URL}/{creado['id']}/enviar", headers=ajeno).status_code == 404
    assert cliente.put(f"{URL}/{creado['id']}", json=INTENDENCIA, headers=ajeno).status_code == 404


# --- Escenarios 5 y 6: bloqueo del COLOGE (409) ---


def test_material_de_guerra_queda_en_borrador_con_envio_bloqueado(cliente, oficial, crear, motor):
    creado = crear(MATERIAL_GUERRA)
    assert creado["estado"] == "BORRADOR"
    assert creado["almacen"]["codigo"] == "SMGE"

    respuesta = cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    assert respuesta.status_code == 409
    error = respuesta.json()
    assert error["codigo"] == "REQUIERE_COLOGE"
    assert error["mensaje"] == (
        "Requiere autorización del COLOGE (disponible en un próximo incremento)."
    )

    despues = cliente.get(f"{URL}/{creado['id']}", headers=oficial).json()
    assert despues["estado"] == "BORRADOR"
    assert despues["monto_total"] is None
    with motor.connect() as conexion:
        assert (
            conexion.scalar(
                text("SELECT version FROM requerimiento WHERE id = :id"), {"id": creado["id"]}
            )
            == 1
        )

    ultimo = historial(motor, creado["id"])[-1]
    assert ultimo["accion"] == "ENVIO_BLOQUEADO"
    assert ultimo["estado_anterior"] == ultimo["estado_nuevo"] == "BORRADOR"
    assert "COLOGE" in ultimo["motivo"]
    assert eventos_auditoria(motor, creado["id"])[-1] == "REQUERIMIENTO.ENVIO_BLOQUEADO"


@pytest.fixture
def umbral_1800(monkeypatch):
    monkeypatch.setattr(obtener_configuracion(), "umbral_monto_alto", Decimal("1800.00"))


def test_monto_en_el_umbral_bloquea_el_envio(cliente, oficial, crear, umbral_1800):
    creado = crear(cuerpo(("INT-002", 10)))  # 10 × 180.00 = 1 800.00, justo el umbral
    respuesta = cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "REQUIERE_COLOGE"


def test_monto_bajo_el_umbral_se_envia(cliente, oficial, crear, umbral_1800):
    creado = crear(cuerpo(("INT-002", 9)))  # 1 620.00
    respuesta = cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    assert respuesta.status_code == 200
    assert respuesta.json()["monto_total"] == "1620.00"


# --- Edición (FR-008) ---


def test_editar_en_borrador(cliente, oficial, crear, motor):
    creado = crear()
    respuesta = cliente.put(f"{URL}/{creado['id']}", json=cuerpo(("INT-004", 3)), headers=oficial)
    assert respuesta.status_code == 200, respuesta.text
    editado = respuesta.json()
    assert editado["estado"] == "BORRADOR"
    assert [(i["item"]["codigo"], i["cantidad_solicitada"]) for i in editado["items"]] == [
        ("INT-004", 3)
    ]
    assert eventos_auditoria(motor, creado["id"])[-1] == "REQUERIMIENTO.EDITAR"


def test_editar_no_cambia_la_categoria(cliente, oficial, crear):
    creado = crear()
    respuesta = cliente.put(f"{URL}/{creado['id']}", json=MATERIAL_GUERRA, headers=oficial)
    assert respuesta.status_code == 422


def test_editar_fuera_de_borrador_responde_409(cliente, oficial, crear):
    creado = crear()
    cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    respuesta = cliente.put(f"{URL}/{creado['id']}", json=INTENDENCIA, headers=oficial)
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TRANSICION_NO_PERMITIDA"


def test_enviar_dos_veces_responde_409(cliente, oficial, crear):
    creado = crear()
    cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    respuesta = cliente.post(f"{URL}/{creado['id']}/enviar", headers=oficial)
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TRANSICION_NO_PERMITIDA"


def test_requerimiento_inexistente_responde_404(cliente, oficial):
    vacio = "00000000-0000-0000-0000-000000000000"
    assert cliente.get(f"{URL}/{vacio}", headers=oficial).status_code == 404
    assert cliente.post(f"{URL}/{vacio}/enviar", headers=oficial).status_code == 404


# --- Bandeja paginada (FR-002, FR-029) ---


def test_bandeja_paginada_solo_muestra_su_unidad(cliente, oficial, crear, login):
    propios = [crear() for _ in range(3)]
    crear(cabeceras=login("oficial.bim12"))
    cliente.post(f"{URL}/{propios[0]['id']}/enviar", headers=oficial)

    primera = cliente.get(URL, params={"size": 2}, headers=oficial).json()
    assert (primera["total"], primera["page"], primera["size"]) == (3, 1, 2)
    assert len(primera["items"]) == 2
    segunda = cliente.get(URL, params={"size": 2, "page": 2}, headers=oficial).json()
    assert len(segunda["items"]) == 1
    vistos = {r["id"] for r in primera["items"] + segunda["items"]}
    assert vistos == {p["id"] for p in propios}
    # Recientes primero.
    assert primera["items"][0]["id"] == propios[-1]["id"]

    borradores = cliente.get(URL, params={"estado": "BORRADOR"}, headers=oficial).json()
    assert borradores["total"] == 2

    otra_unidad = cliente.get(URL, headers=login("oficial.bim12")).json()
    assert otra_unidad["total"] == 1

    # El comandante no ve los BORRADOR; el jefe de la otra División no ve nada.
    assert cliente.get(URL, headers=login("cmdte.bim11")).json()["total"] == 1
    assert cliente.get(URL, headers=login("jlog.2de")).json()["total"] == 0
    assert cliente.get(URL, headers=login("jlog.1de")).json()["total"] == 1
    # El almacén solo ve lo que llegó a su nivel.
    assert cliente.get(URL, headers=login("jalm.sinte")).json()["total"] == 0


def test_bandeja_rechaza_un_tamano_mayor_a_50(cliente, oficial):
    respuesta = cliente.get(URL, params={"size": 51}, headers=oficial)
    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == "size"
