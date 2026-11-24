"""Pruebas de la Fase 2 sobre PostgreSQL: migraciones, disparadores de inmutabilidad (T022),
seeds idempotentes (T023), auditoría encadenada (T028) y Unidad de Trabajo (T012)."""

import uuid

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.unidad_trabajo import UnidadTrabajo
from app.modelos import metadata
from app.modules.audit.dominio.cadena import (
    HUELLA_INICIAL,
    EventoAuditoria,
    calcular_huella,
    contenido_registro,
)
from app.modules.audit.infraestructura.modelos import RegistroAuditoriaModelo
from app.modules.audit.infraestructura.registro_encadenado import RegistroAuditoriaEncadenado
from seeds.cargar import cargar, id_fijo
from tests.integracion.conftest import CONTRASENA_PRUEBAS

# --- Migraciones ---


def test_los_modelos_coinciden_con_las_migraciones(motor):
    with motor.connect() as conexion:
        diferencias = compare_metadata(MigrationContext.configure(conexion), metadata)
    assert diferencias == []


# --- Seeds (data-model.md §9) ---


def test_los_seeds_son_idempotentes(motor):
    def contar() -> tuple:
        with motor.connect() as conexion:
            return conexion.execute(
                text(
                    "SELECT (SELECT count(*) FROM organo), (SELECT count(*) FROM almacen), "
                    "(SELECT count(*) FROM item), (SELECT count(*) FROM usuario), "
                    "(SELECT count(*) FROM movimiento), (SELECT sum(cantidad) FROM stock)"
                )
            ).one()

    antes = contar()
    from app.core.base_datos import obtener_fabrica_sesiones

    with obtener_fabrica_sesiones()() as sesion, sesion.begin():
        resumen = cargar(sesion, CONTRASENA_PRUEBAS)
    assert resumen["usuarios_nuevos"] == 0
    assert contar() == antes
    assert antes[:5] == (10, 2, 14, 15, 14)


def test_el_stock_inicial_cumple_la_invariante_eq03(motor):
    with motor.connect() as conexion:
        diferencias = conexion.scalar(
            text(
                """
                SELECT count(*) FROM stock s
                LEFT JOIN (
                    SELECT almacen_id, item_id,
                           sum(CASE WHEN tipo = 'ENTRADA' THEN cantidad ELSE -cantidad END) AS neto
                    FROM movimiento GROUP BY almacen_id, item_id
                ) m USING (almacen_id, item_id)
                WHERE s.cantidad <> coalesce(m.neto, 0)
                """
            )
        )
    assert diferencias == 0


# --- Disparadores de inmutabilidad (migración 0002) ---


def _insertar_requerimiento(conexion, estado: str) -> uuid.UUID:
    req_id = uuid.uuid4()
    conexion.execute(
        text(
            """
            INSERT INTO requerimiento (id, codigo, unidad_id, gran_unidad_id, almacen_id,
                                       categoria, estado, creado_por)
            VALUES (:id, :codigo, :unidad, :gu, :almacen, 'INTENDENCIA', :estado, :usuario)
            """
        ),
        {
            "id": req_id,
            "codigo": f"REQ-PRUEBA-{req_id.hex[:6]}",
            "unidad": id_fijo("organo", "BIM-11"),
            "gu": id_fijo("organo", "1DE"),
            "almacen": id_fijo("almacen", "SINTE"),
            "estado": estado,
            "usuario": id_fijo("usuario", "oficial.bim11"),
        },
    )
    conexion.execute(
        text(
            "INSERT INTO item_requerimiento (requerimiento_id, item_id, cantidad_solicitada) "
            "VALUES (:r, :i, 5)"
        ),
        {"r": req_id, "i": id_fijo("item", "INT-001")},
    )
    return req_id


def _falla(motor, sql: str, parametros: dict | None = None) -> str:
    with pytest.raises(DBAPIError) as error, motor.begin() as conexion:
        conexion.execute(text(sql), parametros or {})
    return str(error.value.orig)


@pytest.mark.parametrize(
    "operacion", ["UPDATE movimiento SET cantidad = 1", "DELETE FROM movimiento"]
)
def test_movimiento_es_inmutable(motor, operacion):
    assert "inmutable" in _falla(motor, operacion)


def test_historial_firma_acta_y_auditoria_son_inmutables(motor):
    with motor.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO registro_auditoria (tipo_evento, entidad, datos, huella_anterior, "
                "huella, ocurrido_en) VALUES ('PRUEBA', 'prueba', '{}', :h, :h, now())"
            ),
            {"h": HUELLA_INICIAL},
        )
    for tabla in ("historial_requerimiento", "firma", "acta_recepcion", "registro_auditoria"):
        with motor.connect() as conexion:
            disparadores = conexion.scalar(
                text(
                    "SELECT count(*) FROM pg_trigger WHERE tgrelid = CAST(:t AS regclass) "
                    "AND tgname = :n"
                ),
                {"t": tabla, "n": f"tg_{tabla}_inmutable"},
            )
        assert disparadores == 1, tabla
    assert "inmutable" in _falla(motor, "UPDATE registro_auditoria SET tipo_evento = 'X'")
    assert "inmutable" in _falla(motor, "DELETE FROM registro_auditoria")


def test_un_requerimiento_nunca_se_elimina(motor):
    with motor.begin() as conexion:
        req_id = _insertar_requerimiento(conexion, "BORRADOR")
    assert "no se elimina" in _falla(
        motor, "DELETE FROM requerimiento WHERE id = :id", {"id": req_id}
    )


def test_se_permite_la_transicion_a_un_estado_final_y_despues_nada(motor):
    with motor.begin() as conexion:
        req_id = _insertar_requerimiento(conexion, "EN_TRANSITO")
        # Orden de T076: primero los ítems, luego el estado (OLD.estado aún no es final).
        conexion.execute(
            text(
                "UPDATE item_requerimiento SET cantidad_recibida = 5 WHERE requerimiento_id = :id"
            ),
            {"id": req_id},
        )
        conexion.execute(
            text("UPDATE requerimiento SET estado = 'CONFIRMADA' WHERE id = :id"), {"id": req_id}
        )
    parametros = {"id": req_id}
    assert "estado final" in _falla(
        motor, "UPDATE requerimiento SET monto_total = 1 WHERE id = :id", parametros
    )
    assert "estado final" in _falla(
        motor,
        "UPDATE item_requerimiento SET cantidad_recibida = 6 WHERE requerimiento_id = :id",
        parametros,
    )
    assert "estado final" in _falla(
        motor,
        "INSERT INTO item_requerimiento (requerimiento_id, item_id, cantidad_solicitada) "
        f"VALUES (:id, '{id_fijo('item', 'INT-002')}', 1)",
        parametros,
    )


def test_en_borrador_los_items_si_se_pueden_editar(motor):
    with motor.begin() as conexion:
        req_id = _insertar_requerimiento(conexion, "BORRADOR")
        conexion.execute(
            text("DELETE FROM item_requerimiento WHERE requerimiento_id = :id"), {"id": req_id}
        )
        conexion.execute(
            text("UPDATE requerimiento SET version = version + 1 WHERE id = :id"), {"id": req_id}
        )


def test_las_restricciones_check_protegen_los_datos(motor):
    assert "ck_stock_cantidad_no_negativa" in _falla(motor, "UPDATE stock SET cantidad = -1")
    with motor.begin() as conexion:
        req_id = _insertar_requerimiento(conexion, "APROBADA")
    assert "ck_item_requerimiento_despachada_en_rango" in _falla(
        motor,
        "UPDATE item_requerimiento SET cantidad_despachada = 6 WHERE requerimiento_id = :id",
        {"id": req_id},
    )


# --- Auditoría encadenada (ADR-005) ---


def _evento(n: int) -> EventoAuditoria:
    return EventoAuditoria(
        tipo_evento="PRUEBA.EVENTO",
        entidad="requerimiento",
        entidad_id=uuid.uuid4(),
        usuario_id=id_fijo("usuario", "oficial.bim11"),
        rol="OFICIAL_LOGISTICA",
        organo_id=id_fijo("organo", "BIM-11"),
        datos={"n": n, "texto": "ñandú"},
    )


def test_la_auditoria_queda_encadenada_y_se_puede_recalcular():
    with UnidadTrabajo() as uow:
        registro = RegistroAuditoriaEncadenado(uow.sesion)
        huellas = [registro.registrar(_evento(n)) for n in range(3)]

    with UnidadTrabajo() as uow:
        filas = list(
            uow.sesion.scalars(select(RegistroAuditoriaModelo).order_by(RegistroAuditoriaModelo.id))
        )
    assert [f.huella for f in filas] == huellas
    anterior = HUELLA_INICIAL
    for fila in filas:
        assert fila.huella_anterior == anterior
        evento = EventoAuditoria(
            tipo_evento=fila.tipo_evento,
            entidad=fila.entidad,
            entidad_id=fila.entidad_id,
            usuario_id=fila.usuario_id,
            rol=fila.rol.value if fila.rol else None,
            organo_id=fila.organo_id,
            datos=fila.datos,
        )
        assert (
            calcular_huella(anterior, contenido_registro(evento, fila.ocurrido_en)) == fila.huella
        )
        anterior = fila.huella


def test_la_auditoria_se_deshace_si_la_operacion_falla():
    with pytest.raises(RuntimeError), UnidadTrabajo() as uow:
        RegistroAuditoriaEncadenado(uow.sesion).registrar(_evento(1))
        raise RuntimeError("falla del caso de uso")
    with UnidadTrabajo() as uow:
        assert uow.sesion.scalar(select(RegistroAuditoriaModelo.id)) is None


def test_la_unidad_de_trabajo_no_se_usa_cerrada():
    uow = UnidadTrabajo()
    with pytest.raises(RuntimeError):
        _ = uow.sesion
