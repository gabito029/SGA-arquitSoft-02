"""Ayudas compartidas por las pruebas de integración: preparar solicitudes en cada estado."""

import time

from sqlalchemy import text

from seeds.cargar import id_fijo

URL = "/api/v1/requerimientos"

# Quién firma cada nivel para una solicitud de BIM-11 de intendencia.
FIRMANTES_BIM11 = ("cmdte.bim11", "jlog.1de", "jalm.sinte")


def item(codigo: str) -> str:
    return str(id_fijo("item", codigo))


def cuerpo(*lineas: tuple[str, int]) -> dict:
    return {"items": [{"item_id": item(c), "cantidad": n} for c, n in lineas]}


INTENDENCIA = cuerpo(("INT-001", 10), ("INT-002", 5))


def crear_enviada(cliente, login, datos: dict = INTENDENCIA, oficial: str = "oficial.bim11") -> str:
    cabeceras = login(oficial)
    creado = cliente.post(URL, json=datos, headers=cabeceras)
    assert creado.status_code == 201, creado.text
    rid = creado.json()["id"]
    enviado = cliente.post(f"{URL}/{rid}/enviar", headers=cabeceras)
    assert enviado.status_code == 200, enviado.text
    return rid


def firmar(cliente, login, rid: str, usuario: str, decision: str = "APROBAR", motivo=None):
    # Desde 002 la API exige "He revisado el documento" (FR-007).
    cuerpo_firma = {"decision": decision, "documento_revisado": True}
    if motivo is not None:
        cuerpo_firma["motivo"] = motivo
    return cliente.post(f"{URL}/{rid}/firmas", json=cuerpo_firma, headers=login(usuario))


def avanzar(cliente, login, rid: str, niveles: int) -> None:
    """Aprueba los primeros ``niveles`` del conducto regular (1 = VB, 2 = + conformidad, ...)."""
    for usuario in FIRMANTES_BIM11[:niveles]:
        respuesta = firmar(cliente, login, rid, usuario)
        assert respuesta.status_code == 201, respuesta.text


def crear_aprobada(cliente, login, datos: dict = INTENDENCIA) -> str:
    """Solicitud de BIM-11 con los tres niveles del conducto regular aprobados (APROBADA)."""
    rid = crear_enviada(cliente, login, datos)
    avanzar(cliente, login, rid, 3)
    return rid


def despachar(cliente, login, rid: str, cantidades: dict[str, int], usuario="almacenero.sinte"):
    cuerpo_despacho = {
        "items": [{"item_id": item(c), "cantidad": n} for c, n in cantidades.items()]
    }
    return cliente.post(f"{URL}/{rid}/despacho", json=cuerpo_despacho, headers=login(usuario))


def crear_en_transito(cliente, login, datos: dict = INTENDENCIA) -> str:
    """Solicitud APROBADA y despachada completa (EN_TRANSITO)."""
    rid = crear_aprobada(cliente, login, datos)
    cantidades = {
        i["item"]["codigo"]: i["cantidad_solicitada"]
        for i in cliente.get(f"{URL}/{rid}", headers=login("oficial.bim11")).json()["items"]
    }
    respuesta = despachar(cliente, login, rid, cantidades)
    assert respuesta.status_code == 201, respuesta.text
    return rid


def firmar_acta(
    cliente,
    login,
    rid: str,
    recibido: dict[str, int],
    usuario="oficial.bim11",
    observaciones: dict[str, str] | None = None,
):
    observaciones = observaciones or {}
    lineas = []
    for codigo, cantidad in recibido.items():
        linea = {"item_id": item(codigo), "cantidad_recibida": cantidad}
        if codigo in observaciones:
            linea["observacion"] = observaciones[codigo]
        lineas.append(linea)
    return cliente.post(f"{URL}/{rid}/acta", json={"items": lineas}, headers=login(usuario))


def stock(motor, codigo: str, almacen: str = "SINTE") -> int:
    with motor.connect() as conexion:
        return conexion.scalar(
            text("SELECT cantidad FROM stock WHERE almacen_id = :a AND item_id = :i"),
            {"a": id_fijo("almacen", almacen), "i": id_fijo("item", codigo)},
        )


def diferencias_invariante(motor) -> list[dict]:
    """Filas donde stock.cantidad ≠ Σ ENTRADA − Σ SALIDA_DESPACHO (invariante EQ-03)."""
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT s.almacen_id, s.item_id, s.cantidad, COALESCE(SUM(CASE m.tipo "
                "WHEN 'ENTRADA' THEN m.cantidad ELSE -m.cantidad END), 0) AS movimientos "
                "FROM stock s LEFT JOIN movimiento m "
                "ON m.almacen_id = s.almacen_id AND m.item_id = s.item_id "
                "GROUP BY s.almacen_id, s.item_id, s.cantidad "
                "HAVING s.cantidad <> COALESCE(SUM(CASE m.tipo "
                "WHEN 'ENTRADA' THEN m.cantidad ELSE -m.cantidad END), 0)"
            )
        )
        return [dict(f._mapping) for f in filas]


def historial(motor, rid: str) -> list[dict]:
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT h.accion, h.estado_anterior, h.estado_nuevo, u.usuario, h.rol, "
                "o.codigo AS organo, h.motivo, h.ocurrido_en "
                "FROM historial_requerimiento h JOIN usuario u ON u.id = h.usuario_id "
                "JOIN organo o ON o.id = h.organo_id "
                "WHERE h.requerimiento_id = :id ORDER BY h.id"
            ),
            {"id": rid},
        )
        return [dict(f._mapping) for f in filas]


def esperar_bloqueados(motor, cantidad: int, limite_s: float = 10.0) -> None:
    """Espera hasta que ``cantidad`` sesiones estén esperando un bloqueo de fila.

    ``pg_stat_activity`` se congela dentro de una transacción, así que cada consulta va en una
    transacción nueva.
    """
    fin = time.monotonic() + limite_s
    with motor.connect() as conexion:
        while time.monotonic() < fin:
            esperando = conexion.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            )
            conexion.rollback()
            if esperando >= cantidad:
                return
            time.sleep(0.05)
        sesiones = conexion.execute(
            text(
                "SELECT state, wait_event_type, wait_event, left(query, 80) AS q "
                "FROM pg_stat_activity WHERE datname = current_database()"
            )
        ).all()
    raise AssertionError(f"No hubo {cantidad} sesiones esperando el bloqueo: {sesiones}")
