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
    cuerpo_firma = {"decision": decision}
    if motivo is not None:
        cuerpo_firma["motivo"] = motivo
    return cliente.post(f"{URL}/{rid}/firmas", json=cuerpo_firma, headers=login(usuario))


def avanzar(cliente, login, rid: str, niveles: int) -> None:
    """Aprueba los primeros ``niveles`` del conducto regular (1 = VB, 2 = + conformidad, ...)."""
    for usuario in FIRMANTES_BIM11[:niveles]:
        respuesta = firmar(cliente, login, rid, usuario)
        assert respuesta.status_code == 201, respuesta.text


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
    """Espera hasta que ``cantidad`` sesiones estén esperando un bloqueo de fila."""
    fin = time.monotonic() + limite_s
    with motor.connect() as conexion:
        while time.monotonic() < fin:
            esperando = conexion.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            )
            if esperando >= cantidad:
                return
            time.sleep(0.05)
    raise AssertionError(f"No hubo {cantidad} sesiones esperando el bloqueo")
