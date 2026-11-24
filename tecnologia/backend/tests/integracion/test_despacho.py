"""T066 — US3: aprobación del almacén y despacho sin superar el stock (escenarios 1 a 4 y 6 de
spec.md; FR-011, FR-017 a FR-020) contra la API y PostgreSQL reales."""

from sqlalchemy import text

from tests.integracion.apoyo import (
    URL,
    avanzar,
    crear_aprobada,
    crear_enviada,
    cuerpo,
    despachar,
    diferencias_invariante,
    firmar,
    historial,
    stock,
)

PONCHOS_7 = cuerpo(("INT-010", 7))  # INT-010 tiene stock 10 en los seeds


def movimientos(motor, rid: str) -> list[tuple[str, int]]:
    with motor.connect() as conexion:
        return [
            (f.tipo, f.cantidad)
            for f in conexion.execute(
                text("SELECT tipo, cantidad FROM movimiento WHERE requerimiento_id = :id"),
                {"id": rid},
            )
        ]


# --- Escenarios 1 y 2: el jefe de almacén aprueba o rechaza ---


def test_el_jefe_de_almacen_aprueba_con_firma(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 2)
    respuesta = firmar(cliente, login, rid, "jalm.sinte")
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["estado"] == "APROBADA"
    detalle = cliente.get(f"{URL}/{rid}", headers=login("almacenero.sinte")).json()
    assert detalle["acciones_disponibles"] == ["DESPACHAR"]
    niveles = [
        f["nivel"] for f in cliente.get(f"{URL}/{rid}/firmas", headers=login("jalm.sinte")).json()
    ]
    assert niveles == ["VB_UNIDAD", "CONFORMIDAD_GU", "APROBACION_ALMACEN"]


def test_el_jefe_de_almacen_rechaza_con_motivo(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 2)
    respuesta = firmar(cliente, login, rid, "jalm.sinte", "RECHAZAR", "Stock insuficiente")
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["estado"] == "RECHAZADA"
    ultimo = historial(motor, rid)[-1]
    assert (ultimo["accion"], ultimo["motivo"]) == ("RECHAZAR", "Stock insuficiente")
    # El almacén sigue viendo lo que rechazó en su nivel.
    assert cliente.get(f"{URL}/{rid}", headers=login("almacenero.sinte")).status_code == 200


def test_otro_almacen_no_aprueba(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 2)
    assert firmar(cliente, login, rid, "jalm.smge").status_code == 404


# --- Escenario 3: despacho que descuenta el stock ---


def test_despachar_7_con_stock_10_deja_3(cliente, login, motor):
    rid = crear_aprobada(cliente, login, PONCHOS_7)
    assert stock(motor, "INT-010") == 10
    respuesta = despachar(cliente, login, rid, {"INT-010": 7})
    assert respuesta.status_code == 201, respuesta.text
    cuerpo_respuesta = respuesta.json()
    assert cuerpo_respuesta["estado"] == "EN_TRANSITO"
    assert cuerpo_respuesta["items"][0]["cantidad_despachada"] == 7
    assert stock(motor, "INT-010") == 3
    assert movimientos(motor, rid) == [("SALIDA_DESPACHO", 7)]
    assert diferencias_invariante(motor) == []

    ultimo = historial(motor, rid)[-1]
    assert (ultimo["accion"], ultimo["estado_anterior"], ultimo["estado_nuevo"]) == (
        "DESPACHAR",
        "APROBADA",
        "EN_TRANSITO",
    )
    assert ultimo["usuario"] == "almacenero.sinte"
    # Ahora le toca al oficial de la unidad firmar el acta.
    detalle = cliente.get(f"{URL}/{rid}", headers=login("oficial.bim11")).json()
    assert detalle["acciones_disponibles"] == ["FIRMAR_ACTA"]


def test_despacho_parcial_registra_lo_despachado(cliente, login, motor):
    rid = crear_aprobada(cliente, login)  # INT-001 × 10 e INT-002 × 5
    respuesta = despachar(cliente, login, rid, {"INT-001": 6, "INT-002": 0})
    assert respuesta.status_code == 201, respuesta.text
    despachado = {i["item"]["codigo"]: i["cantidad_despachada"] for i in respuesta.json()["items"]}
    assert despachado == {"INT-001": 6, "INT-002": 0}
    # Solo se mueve lo que se despachó (un movimiento con cantidad 0 no existe).
    assert movimientos(motor, rid) == [("SALIDA_DESPACHO", 6)]
    assert stock(motor, "INT-001") == 494
    assert stock(motor, "INT-002") == 200


# --- Escenario 4: stock insuficiente, nada cambia ---


def test_stock_insuficiente_responde_409_y_nada_cambia(cliente, login, motor):
    rid = crear_aprobada(cliente, login, cuerpo(("INT-010", 7), ("INT-001", 5)))
    with motor.begin() as conexion:
        # El stock del poncho bajó a 5 después de aprobar (por ejemplo, otro despacho).
        conexion.execute(
            text(
                "UPDATE stock SET cantidad = 5 WHERE item_id = "
                "(SELECT id FROM item WHERE codigo = 'INT-010')"
            )
        )
    antes_001 = stock(motor, "INT-001")
    respuesta = despachar(cliente, login, rid, {"INT-010": 7, "INT-001": 5})
    assert respuesta.status_code == 409, respuesta.text
    error = respuesta.json()
    assert error["codigo"] == "STOCK_INSUFICIENTE"
    assert "stock" in error["mensaje"].lower()
    assert error["detalles"] and "Stock disponible: 5" in error["detalles"][0]["mensaje"]

    assert stock(motor, "INT-010") == 5
    assert stock(motor, "INT-001") == antes_001  # tampoco el ítem que sí alcanzaba
    assert movimientos(motor, rid) == []
    detalle = cliente.get(f"{URL}/{rid}", headers=login("almacenero.sinte")).json()
    assert detalle["estado"] == "APROBADA"
    assert all(i["cantidad_despachada"] is None for i in detalle["items"])
    assert historial(motor, rid)[-1]["accion"] == "FIRMAR"


# --- Escenario 6: solo se despacha lo APROBADO ---


def test_despachar_algo_que_no_esta_aprobado_responde_409(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 2)  # PENDIENTE_APROBACION: el almacenero ya la ve
    respuesta = despachar(cliente, login, rid, {"INT-001": 10, "INT-002": 5})
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TRANSICION_NO_PERMITIDA"
    assert movimientos(motor, rid) == []


def test_despachar_dos_veces_responde_409(cliente, login, motor):
    rid = crear_aprobada(cliente, login, PONCHOS_7)
    assert despachar(cliente, login, rid, {"INT-010": 7}).status_code == 201
    respuesta = despachar(cliente, login, rid, {"INT-010": 3})
    assert respuesta.status_code == 409
    assert stock(motor, "INT-010") == 3


# --- Validaciones (422) ---


def test_despachar_mas_de_lo_solicitado_responde_422(cliente, login, motor):
    rid = crear_aprobada(cliente, login, PONCHOS_7)
    respuesta = despachar(cliente, login, rid, {"INT-010": 8})
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "CANTIDAD_INVALIDA"
    assert stock(motor, "INT-010") == 10


def test_despachar_todo_en_cero_responde_422(cliente, login):
    rid = crear_aprobada(cliente, login, PONCHOS_7)
    assert despachar(cliente, login, rid, {"INT-010": 0}).status_code == 422


def test_despacho_debe_cubrir_los_items_de_la_solicitud(cliente, login):
    rid = crear_aprobada(cliente, login)
    assert despachar(cliente, login, rid, {"INT-001": 10}).status_code == 422
    assert (
        despachar(cliente, login, rid, {"INT-001": 1, "INT-002": 1, "INT-003": 1}).status_code
        == 422
    )


def test_despacho_con_cantidad_negativa_o_repetida_responde_422(cliente, login):
    rid = crear_aprobada(cliente, login, PONCHOS_7)
    cabeceras = login("almacenero.sinte")
    negativa = {"items": [{"item_id": str(_item("INT-010")), "cantidad": -1}]}
    assert (
        cliente.post(f"{URL}/{rid}/despacho", json=negativa, headers=cabeceras).status_code == 422
    )
    repetida = {"items": [{"item_id": str(_item("INT-010")), "cantidad": 1}] * 2}
    assert (
        cliente.post(f"{URL}/{rid}/despacho", json=repetida, headers=cabeceras).status_code == 422
    )
    assert (
        cliente.post(f"{URL}/{rid}/despacho", json={"items": []}, headers=cabeceras).status_code
        == 422
    )


def _item(codigo: str):
    from seeds.cargar import id_fijo

    return id_fijo("item", codigo)


# --- Acceso ---


def test_solo_el_almacenero_del_almacen_despacha(cliente, login):
    rid = crear_aprobada(cliente, login, PONCHOS_7)
    for usuario in ("jalm.sinte", "oficial.bim11", "cmdte.bim11", "jlog.1de", "auditor"):
        assert despachar(cliente, login, rid, {"INT-010": 7}, usuario).status_code == 403, usuario
    assert despachar(cliente, login, rid, {"INT-010": 7}, "almacenero.smge").status_code == 404


# --- Stock del almacén ---


def test_stock_del_almacen_del_usuario(cliente, login):
    respuesta = cliente.get(
        "/api/v1/inventario/stock", params={"size": 50}, headers=login("jalm.sinte")
    )
    assert respuesta.status_code == 200
    pagina = respuesta.json()
    assert pagina["total"] == 10  # los 10 ítems de intendencia
    assert {s["item"]["categoria"] for s in pagina["items"]} == {"INTENDENCIA"}
    ponchos = next(s for s in pagina["items"] if s["item"]["codigo"] == "INT-010")
    assert ponchos["cantidad"] == 10

    smge = cliente.get("/api/v1/inventario/stock", headers=login("almacenero.smge")).json()
    assert smge["total"] == 4
    primera = cliente.get(
        "/api/v1/inventario/stock", params={"size": 3}, headers=login("jalm.sinte")
    )
    assert len(primera.json()["items"]) == 3


def test_stock_solo_para_roles_de_almacen(cliente, login):
    assert cliente.get("/api/v1/inventario/stock").status_code == 401
    for usuario in ("oficial.bim11", "cmdte.bim11", "auditor"):
        respuesta = cliente.get("/api/v1/inventario/stock", headers=login(usuario))
        assert respuesta.status_code == 403, usuario
