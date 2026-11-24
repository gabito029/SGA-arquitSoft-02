"""T056 — US2: aprobar o rechazar por el conducto regular (escenarios 1 a 6 de spec.md; FR-009 a
FR-016) contra la API y PostgreSQL reales, con el firmador Ed25519 real."""

import hashlib
import threading

from sqlalchemy import text

from tests.integracion.apoyo import (
    URL,
    avanzar,
    crear_enviada,
    esperar_bloqueados,
    firmar,
    historial,
)


def estado(cliente, login, rid: str, usuario: str = "oficial.bim11") -> str:
    return cliente.get(f"{URL}/{rid}", headers=login(usuario)).json()["estado"]


# --- Escenario 1: visto bueno ---


def test_visto_bueno_del_comandante(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    respuesta = firmar(cliente, login, rid, "cmdte.bim11")
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "PENDIENTE_CONFORMIDAD"
    assert cuerpo["acciones_disponibles"] == []

    ultimo = historial(motor, rid)[-1]
    assert (ultimo["accion"], ultimo["estado_anterior"], ultimo["estado_nuevo"]) == (
        "FIRMAR",
        "PENDIENTE_VB_UNIDAD",
        "PENDIENTE_CONFORMIDAD",
    )
    assert (ultimo["usuario"], ultimo["organo"], ultimo["rol"]) == (
        "cmdte.bim11",
        "BIM-11",
        "COMANDANTE_UNIDAD",
    )
    assert ultimo["ocurrido_en"] is not None

    firmas = cliente.get(f"{URL}/{rid}/firmas", headers=login("oficial.bim11")).json()
    assert len(firmas) == 1
    firma = firmas[0]
    assert (firma["nivel"], firma["decision"], firma["rol"]) == (
        "VB_UNIDAD",
        "APROBAR",
        "COMANDANTE_UNIDAD",
    )
    assert firma["firmante"] == "Comandante BIM-11"
    assert firma["organo"]["codigo"] == "BIM-11"
    assert firma["metodo"] == "ed25519-sha256-v1"
    assert len(firma["huella_sha256"]) == 64


def test_la_firma_guardada_se_verifica_con_la_clave_del_sistema(cliente, login, motor, firmador):
    rid = crear_enviada(cliente, login)
    firmar(cliente, login, rid, "cmdte.bim11")
    with motor.connect() as conexion:
        fila = conexion.execute(
            text("SELECT contenido_canonico, firma, clave_id, huella_sha256 FROM firma")
        ).one()
    contenido = fila.contenido_canonico.encode()
    assert fila.clave_id == firmador.clave_id
    assert firmador.verificar(contenido, fila.firma, fila.clave_id)
    assert '"estado"' not in fila.contenido_canonico
    assert '"version"' not in fila.contenido_canonico
    assert fila.huella_sha256 == hashlib.sha256(contenido).hexdigest()


def test_auditoria_registra_la_firma(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    firmar(cliente, login, rid, "cmdte.bim11")
    with motor.connect() as conexion:
        eventos = list(
            conexion.scalars(
                text(
                    "SELECT tipo_evento FROM registro_auditoria WHERE entidad_id = :id ORDER BY id"
                ),
                {"id": rid},
            )
        )
    assert eventos[-1] == "REQUERIMIENTO.FIRMAR"


# --- Escenario 2: conformidad ---


def test_conformidad_del_jefe_de_logistica(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    respuesta = firmar(cliente, login, rid, "jlog.1de")
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["estado"] == "PENDIENTE_APROBACION"
    # Ahora le toca al almacén.
    detalle = cliente.get(f"{URL}/{rid}", headers=login("jalm.sinte")).json()
    assert detalle["acciones_disponibles"] == ["FIRMAR", "RECHAZAR"]
    niveles = [
        f["nivel"] for f in cliente.get(f"{URL}/{rid}/firmas", headers=login("auditor")).json()
    ]
    assert niveles == ["VB_UNIDAD", "CONFORMIDAD_GU"]


# --- Escenario 3: no se salta un nivel ---


def test_conformidad_antes_del_visto_bueno_responde_409(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    respuesta = firmar(cliente, login, rid, "jlog.1de")
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TRANSICION_NO_PERMITIDA"
    assert estado(cliente, login, rid) == "PENDIENTE_VB_UNIDAD"
    with motor.connect() as conexion:
        assert conexion.scalar(text("SELECT count(*) FROM firma")) == 0


def test_el_comandante_no_firma_la_conformidad(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    respuesta = firmar(cliente, login, rid, "cmdte.bim11")
    assert respuesta.status_code == 409


# --- Escenario 4: otra jurisdicción responde como si no existiera ---


def test_jefe_de_otra_division_recibe_404(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    otro = login("jlog.2de")
    assert cliente.get(f"{URL}/{rid}", headers=otro).status_code == 404
    assert cliente.get(f"{URL}/{rid}/firmas", headers=otro).status_code == 404
    respuesta = firmar(cliente, login, rid, "jlog.2de")
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "NO_ENCONTRADO"
    assert estado(cliente, login, rid) == "PENDIENTE_CONFORMIDAD"


def test_comandante_de_otra_unidad_recibe_404(cliente, login):
    rid = crear_enviada(cliente, login)
    assert firmar(cliente, login, rid, "cmdte.bim12").status_code == 404


def test_roles_que_no_firman_reciben_403(cliente, login):
    rid = crear_enviada(cliente, login)
    for usuario in ("oficial.bim11", "almacenero.sinte", "auditor"):
        respuesta = firmar(cliente, login, rid, usuario)
        assert respuesta.status_code == 403, usuario
        assert respuesta.json()["codigo"] == "SIN_PERMISO"


def test_sin_sesion_responde_401(cliente, login):
    rid = crear_enviada(cliente, login)
    assert cliente.post(f"{URL}/{rid}/firmas", json={"decision": "APROBAR"}).status_code == 401
    assert cliente.get(f"{URL}/{rid}/firmas").status_code == 401


# --- Escenario 5: rechazo con motivo ---


def test_rechazo_sin_motivo_responde_422_y_no_cambia_nada(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    for motivo in (None, "   ", ""):
        respuesta = firmar(cliente, login, rid, "cmdte.bim11", "RECHAZAR", motivo)
        assert respuesta.status_code == 422, motivo
        assert "motivo" in [d["campo"] for d in respuesta.json()["detalles"]]
    assert estado(cliente, login, rid) == "PENDIENTE_VB_UNIDAD"
    with motor.connect() as conexion:
        assert conexion.scalar(text("SELECT count(*) FROM firma")) == 0


def test_rechazo_con_motivo_deja_rechazada_y_nadie_mas_actua(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 1)
    motivo = "La cantidad no corresponde a la dotación"
    respuesta = firmar(cliente, login, rid, "jlog.1de", "RECHAZAR", motivo)
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["estado"] == "RECHAZADA"
    assert respuesta.json()["acciones_disponibles"] == []

    ultimo = historial(motor, rid)[-1]
    assert (ultimo["accion"], ultimo["estado_anterior"], ultimo["motivo"]) == (
        "RECHAZAR",
        "PENDIENTE_CONFORMIDAD",
        motivo,
    )
    firmas = cliente.get(f"{URL}/{rid}/firmas", headers=login("jlog.1de")).json()
    assert [(f["nivel"], f["decision"]) for f in firmas] == [
        ("VB_UNIDAD", "APROBAR"),
        ("CONFORMIDAD_GU", "RECHAZAR"),
    ]
    # Ningún otro nivel puede actuar sobre una solicitud rechazada.
    assert firmar(cliente, login, rid, "jlog.1de").status_code == 409
    assert firmar(cliente, login, rid, "cmdte.bim11").status_code == 409
    assert firmar(cliente, login, rid, "jalm.sinte").status_code == 404  # no llegó al almacén
    assert cliente.post(f"{URL}/{rid}/enviar", headers=login("oficial.bim11")).status_code == 409


def test_motivo_demasiado_largo_responde_422(cliente, login):
    rid = crear_enviada(cliente, login)
    respuesta = firmar(cliente, login, rid, "cmdte.bim11", "RECHAZAR", "x" * 501)
    assert respuesta.status_code == 422


# --- Escenario 6: cada nivel firma una sola vez ---


def test_doble_firma_responde_nivel_ya_firmado(cliente, login, motor):
    rid = crear_enviada(cliente, login)
    assert firmar(cliente, login, rid, "cmdte.bim11").status_code == 201
    respuesta = firmar(cliente, login, rid, "cmdte.bim11")
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "NIVEL_YA_FIRMADO"
    respuesta = firmar(cliente, login, rid, "cmdte.bim11", "RECHAZAR", "Cambio de opinión")
    assert respuesta.json()["codigo"] == "NIVEL_YA_FIRMADO"
    with motor.connect() as conexion:
        assert conexion.scalar(text("SELECT count(*) FROM firma")) == 1


def test_firmas_concurrentes_registran_una_sola(cliente, login, motor):
    """Dos firmas a la vez: una se registra (201) y la otra recibe 409 ESTADO_CAMBIADO."""
    rid = crear_enviada(cliente, login)
    cabeceras = login("cmdte.bim11")
    respuestas: list = []

    def firmar_en_hilo() -> None:
        respuestas.append(
            cliente.post(f"{URL}/{rid}/firmas", json={"decision": "APROBAR"}, headers=cabeceras)
        )

    # Se retiene el bloqueo de la fila para que las dos peticiones lleguen a la vez a esperarlo.
    with motor.connect() as retenedor:
        transaccion = retenedor.begin()
        retenedor.execute(
            text("SELECT id FROM requerimiento WHERE id = :id FOR UPDATE"), {"id": rid}
        )
        hilos = [threading.Thread(target=firmar_en_hilo) for _ in range(2)]
        for hilo in hilos:
            hilo.start()
        esperar_bloqueados(motor, 2)
        transaccion.commit()
    for hilo in hilos:
        hilo.join(timeout=30)

    codigos = sorted(r.status_code for r in respuestas)
    assert codigos == [201, 409], [r.text for r in respuestas]
    perdedora = next(r for r in respuestas if r.status_code == 409)
    assert perdedora.json()["codigo"] == "ESTADO_CAMBIADO"
    with motor.connect() as conexion:
        assert conexion.scalar(text("SELECT count(*) FROM firma")) == 1
        assert (
            conexion.scalar(
                text("SELECT count(*) FROM historial_requerimiento WHERE accion = 'FIRMAR'")
            )
            == 1
        )
    assert estado(cliente, login, rid) == "PENDIENTE_CONFORMIDAD"
