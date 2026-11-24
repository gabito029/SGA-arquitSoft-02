"""T081 — EQ-08 (adaptada a 001): trazabilidad completa (FR-026 a FR-028; ADR-005).

- Recorre el flujo: envío, visto bueno, conformidad, aprobación, despacho y acta.
- ``/historial`` muestra los 6 pasos en orden, y la consulta SQL confirma usuario, rol, órgano y
  fecha en el 100 % de ellos.
- La cadena de ``registro_auditoria`` está íntegra: se recalcula cada huella.
- No existe ningún endpoint para borrar o editar el historial.

El resultado se guarda en ``evidencias/EQ-08/``.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from app.modules.audit.dominio.cadena import (
    HUELLA_INICIAL,
    EventoAuditoria,
    calcular_huella,
    contenido_registro,
)
from tests.integracion.apoyo import URL, crear_en_transito, firmar_acta

EVIDENCIA = Path(__file__).resolve().parents[4] / "evidencias" / "EQ-08" / "resumen-eq08.json"

PASOS_ESPERADOS = [
    ("ENVIAR", "BORRADOR", "PENDIENTE_VB_UNIDAD", "oficial.bim11", "OFICIAL_LOGISTICA", "BIM-11"),
    (
        "FIRMAR",
        "PENDIENTE_VB_UNIDAD",
        "PENDIENTE_CONFORMIDAD",
        "cmdte.bim11",
        "COMANDANTE_UNIDAD",
        "BIM-11",
    ),
    (
        "FIRMAR",
        "PENDIENTE_CONFORMIDAD",
        "PENDIENTE_APROBACION",
        "jlog.1de",
        "JEFE_LOGISTICA_GU",
        "1DE",
    ),
    ("FIRMAR", "PENDIENTE_APROBACION", "APROBADA", "jalm.sinte", "JEFE_ALMACEN", "SINTE"),
    ("DESPACHAR", "APROBADA", "EN_TRANSITO", "almacenero.sinte", "ALMACENERO", "SINTE"),
    ("FIRMAR_ACTA", "EN_TRANSITO", "CONFIRMADA", "oficial.bim11", "OFICIAL_LOGISTICA", "BIM-11"),
]


def _cadena_integra(motor) -> tuple[int, list[int]]:
    """Recalcula la cadena completa; devuelve (registros, ids que no cuadran)."""
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT id, tipo_evento, entidad, entidad_id, usuario_id, rol, organo_id, datos, "
                "huella_anterior, huella, ocurrido_en FROM registro_auditoria ORDER BY id"
            )
        ).all()
    rotos = []
    anterior = HUELLA_INICIAL
    for f in filas:
        evento = EventoAuditoria(
            tipo_evento=f.tipo_evento,
            entidad=f.entidad,
            entidad_id=f.entidad_id,
            usuario_id=f.usuario_id,
            rol=f.rol,
            organo_id=f.organo_id,
            datos=f.datos,
        )
        esperada = calcular_huella(anterior, contenido_registro(evento, f.ocurrido_en))
        if f.huella_anterior != anterior or f.huella != esperada:
            rotos.append(f.id)
        anterior = f.huella
    return len(filas), rotos


def test_trazabilidad_del_flujo_completo(cliente, login, motor):
    rid = crear_en_transito(cliente, login)
    assert firmar_acta(cliente, login, rid, {"INT-001": 10, "INT-002": 5}).status_code == 201

    # 1. La línea de tiempo por API, en orden.
    respuesta = cliente.get(f"{URL}/{rid}/historial", headers=login("oficial.bim11"))
    assert respuesta.status_code == 200, respuesta.text
    linea = respuesta.json()
    assert linea[0]["accion"] == "CREAR"
    pasos = linea[1:]
    assert [(p["accion"], p["estado_anterior"], p["estado_nuevo"]) for p in pasos] == [
        p[:3] for p in PASOS_ESPERADOS
    ]
    fechas = [p["ocurrido_en"] for p in linea]
    assert fechas == sorted(fechas)
    assert all(p["usuario"] and p["organo"]["codigo"] and p["rol"] for p in pasos)

    # 2. La consulta SQL confirma usuario, rol, órgano y fecha en el 100 % de los pasos.
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT h.accion::text, h.estado_anterior::text, h.estado_nuevo::text, u.usuario, "
                "h.rol::text, o.codigo, h.ocurrido_en FROM historial_requerimiento h "
                "JOIN usuario u ON u.id = h.usuario_id JOIN organo o ON o.id = h.organo_id "
                "WHERE h.requerimiento_id = :id AND h.accion <> 'CREAR' "
                "ORDER BY h.ocurrido_en, h.id"
            ),
            {"id": rid},
        ).all()
    confirmados = [
        tuple(f[:6]) == esperado and f.ocurrido_en is not None
        for f, esperado in zip(filas, PASOS_ESPERADOS, strict=True)
    ]
    assert all(confirmados)

    # 3. La cadena de auditoría está íntegra.
    registros, rotos = _cadena_integra(motor)
    assert registros >= 7  # CREAR + los 6 pasos
    assert rotos == []

    # 4. No hay endpoints para editar o borrar el historial.
    from app.main import app

    escrituras = [
        (ruta.path, sorted(ruta.methods))
        for ruta in app.routes
        if "historial" in getattr(ruta, "path", "") and set(ruta.methods) - {"GET", "HEAD"}
    ]
    assert escrituras == []
    cabeceras = login("auditor")
    for metodo in ("DELETE", "PUT", "PATCH", "POST"):
        r = cliente.request(metodo, f"{URL}/{rid}/historial", headers=cabeceras)
        assert r.status_code == 405, metodo

    EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCIA.write_text(
        json.dumps(
            {
                "escenario": "EQ-08 trazabilidad del flujo completo (incremento 001)",
                "generado_en": datetime.now(UTC).isoformat(timespec="seconds"),
                "pasos": [
                    {
                        "accion": p["accion"],
                        "estado_anterior": p["estado_anterior"],
                        "estado_nuevo": p["estado_nuevo"],
                        "usuario": p["usuario"],
                        "rol": p["rol"],
                        "organo": p["organo"]["codigo"],
                        "ocurrido_en": p["ocurrido_en"],
                    }
                    for p in pasos
                ],
                "pasos_confirmados_por_sql": f"{sum(confirmados)}/{len(PASOS_ESPERADOS)}",
                "porcentaje": round(100 * sum(confirmados) / len(PASOS_ESPERADOS), 2),
                "cadena_auditoria": {"registros": registros, "huellas_que_no_cuadran": rotos},
                "endpoints_de_escritura_sobre_historial": escrituras,
                "cumple": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_la_cadena_detecta_un_registro_alterado(cliente, login, motor):
    crear_en_transito(cliente, login)
    _, rotos = _cadena_integra(motor)
    assert rotos == []
    with motor.begin() as conexion:
        conexion.execute(
            text("ALTER TABLE registro_auditoria DISABLE TRIGGER tg_registro_auditoria_inmutable")
        )
        conexion.execute(
            text(
                "UPDATE registro_auditoria SET datos = datos || '{\"alterado\": true}' "
                "WHERE id = (SELECT min(id) + 1 FROM registro_auditoria)"
            )
        )
        conexion.execute(
            text("ALTER TABLE registro_auditoria ENABLE TRIGGER tg_registro_auditoria_inmutable")
        )
    _, rotos = _cadena_integra(motor)
    assert len(rotos) == 1


def test_historial_respeta_la_jurisdiccion_y_muestra_el_motivo(cliente, login):
    from tests.integracion.apoyo import crear_enviada, firmar

    rid = crear_enviada(cliente, login)
    firmar(cliente, login, rid, "cmdte.bim11", "RECHAZAR", "Fuera de la dotación")
    linea = cliente.get(f"{URL}/{rid}/historial", headers=login("cmdte.bim11")).json()
    assert linea[-1]["accion"] == "RECHAZAR"
    assert linea[-1]["motivo"] == "Fuera de la dotación"
    assert linea[-1]["organo"]["codigo"] == "BIM-11"
    assert cliente.get(f"{URL}/{rid}/historial", headers=login("oficial.bim21")).status_code == 404
    assert cliente.get(f"{URL}/{rid}/historial", headers=login("jlog.2de")).status_code == 404
    assert cliente.get(f"{URL}/{rid}/historial").status_code == 401
