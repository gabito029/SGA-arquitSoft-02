"""T075 — EQ-02: integridad de las firmas (FR-024, FR-025; research §3).

Para cada dato firmado (cantidad recibida, cantidad solicitada, firmante, fecha y otros), la
prueba desactiva el disparador de inmutabilidad dentro de su transacción, altera el dato en la
base de datos y comprueba que ``/verificacion`` responde ALTERADA: debe ocurrir en el 100 % de los
casos. También comprueba lo contrario, para descartar falsos positivos: después del despacho
(EN_TRANSITO) y del acta (CONFIRMADA), las firmas VB_UNIDAD, CONFORMIDAD_GU y APROBACION_ALMACEN
siguen dando INTEGRA. El resumen se guarda en ``evidencias/EQ-02/``.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text

from tests.integracion.apoyo import URL, avanzar, crear_en_transito, crear_enviada, firmar_acta

EVIDENCIA = Path(__file__).resolve().parents[4] / "evidencias" / "EQ-02" / "resumen-eq02.json"
RESULTADOS: list[dict] = []

NIVELES_PREVIOS = ["VB_UNIDAD", "CONFORMIDAD_GU", "APROBACION_ALMACEN"]


@pytest.fixture(scope="module", autouse=True)
def resumen():
    RESULTADOS.clear()
    yield
    if not RESULTADOS:
        return
    cumplidos = sum(1 for r in RESULTADOS if r["cumple"])
    EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCIA.write_text(
        json.dumps(
            {
                "escenario": "EQ-02 integridad de firmas y del acta (incremento 001)",
                "generado_en": datetime.now(UTC).isoformat(timespec="seconds"),
                "casos": len(RESULTADOS),
                "cumplidos": cumplidos,
                "porcentaje": round(100 * cumplidos / len(RESULTADOS), 2),
                "resultados": RESULTADOS,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def verificar(cliente, login, rid: str) -> dict:
    respuesta = cliente.get(f"{URL}/{rid}/verificacion", headers=login("auditor"))
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def por_nivel(verificacion: dict) -> dict[str, str]:
    return {f["nivel"]: f["resultado"] for f in verificacion["firmas"]}


def alterar(motor, tabla: str, disparador: str, sentencia: str, parametros: dict) -> None:
    """Altera un dato saltándose el disparador solo dentro de esta transacción."""
    with motor.begin() as conexion:
        conexion.execute(text(f"ALTER TABLE {tabla} DISABLE TRIGGER {disparador}"))
        filas = conexion.execute(text(sentencia), parametros).rowcount
        conexion.execute(text(f"ALTER TABLE {tabla} ENABLE TRIGGER {disparador}"))
    assert filas >= 1, sentencia


ITEMS = "item_requerimiento", "tg_item_requerimiento_protegido"
FIRMA = "firma", "tg_firma_inmutable"

# (caso, tabla y disparador, sentencia, niveles que deben quedar ALTERADA)
ALTERACIONES = [
    (
        "cantidad_recibida",
        ITEMS,
        "UPDATE item_requerimiento SET cantidad_recibida = cantidad_recibida + 1 "
        "WHERE requerimiento_id = :id AND item_id = (SELECT id FROM item WHERE codigo = 'INT-001')",
        {"ACTA_RECEPCION"},
    ),
    (
        "cantidad_solicitada",
        ITEMS,
        "UPDATE item_requerimiento SET cantidad_solicitada = cantidad_solicitada + 1 "
        "WHERE requerimiento_id = :id AND item_id = (SELECT id FROM item WHERE codigo = 'INT-002')",
        {"VB_UNIDAD", "CONFORMIDAD_GU", "APROBACION_ALMACEN", "ACTA_RECEPCION"},
    ),
    (
        "cantidad_despachada",
        ITEMS,
        "UPDATE item_requerimiento SET cantidad_despachada = cantidad_despachada - 1 "
        "WHERE requerimiento_id = :id AND item_id = (SELECT id FROM item WHERE codigo = 'INT-001')",
        {"ACTA_RECEPCION"},
    ),
    (
        "observacion",
        ITEMS,
        "UPDATE item_requerimiento SET observacion = 'Todo conforme' WHERE requerimiento_id = :id",
        {"ACTA_RECEPCION"},
    ),
    (
        "firmante_acta",
        FIRMA,
        "UPDATE firma SET firmante_id = (SELECT id FROM usuario WHERE usuario = 'oficial.bim12') "
        "WHERE requerimiento_id = :id AND nivel = 'ACTA_RECEPCION'",
        {"ACTA_RECEPCION"},
    ),
    (
        "firmante_vb",
        FIRMA,
        "UPDATE firma SET firmante_id = (SELECT id FROM usuario WHERE usuario = 'cmdte.bim12') "
        "WHERE requerimiento_id = :id AND nivel = 'VB_UNIDAD'",
        {"VB_UNIDAD"},
    ),
    (
        "fecha_acta",
        FIRMA,
        "UPDATE firma SET firmado_en = firmado_en + interval '1 second' "
        "WHERE requerimiento_id = :id AND nivel = 'ACTA_RECEPCION'",
        {"ACTA_RECEPCION"},
    ),
    (
        "fecha_conformidad",
        FIRMA,
        "UPDATE firma SET firmado_en = firmado_en - interval '1 day' "
        "WHERE requerimiento_id = :id AND nivel = 'CONFORMIDAD_GU'",
        {"CONFORMIDAD_GU"},
    ),
    (
        "decision",
        FIRMA,
        "UPDATE firma SET decision = 'RECHAZAR' "
        "WHERE requerimiento_id = :id AND nivel = 'APROBACION_ALMACEN'",
        {"APROBACION_ALMACEN"},
    ),
    (
        "bytes_de_la_firma",
        FIRMA,
        "UPDATE firma SET firma = translate(firma, 'ABCabc', 'BCAbca') "
        "WHERE requerimiento_id = :id AND nivel = 'ACTA_RECEPCION'",
        {"ACTA_RECEPCION"},
    ),
    (
        "huella",
        FIRMA,
        "UPDATE firma SET huella_sha256 = repeat('0', 64) "
        "WHERE requerimiento_id = :id AND nivel = 'VB_UNIDAD'",
        {"VB_UNIDAD"},
    ),
]


def confirmada(cliente, login) -> str:
    rid = crear_en_transito(cliente, login)
    respuesta = firmar_acta(
        cliente, login, rid, {"INT-001": 9, "INT-002": 5}, observaciones={"INT-001": "Falta 1"}
    )
    assert respuesta.status_code == 201, respuesta.text
    return rid


@pytest.mark.parametrize(
    ("caso", "tabla_disparador", "sentencia", "alteradas"),
    ALTERACIONES,
    ids=[a[0] for a in ALTERACIONES],
)
def test_alterar_un_dato_firmado_da_alterada(
    cliente, login, motor, caso, tabla_disparador, sentencia, alteradas
):
    rid = confirmada(cliente, login)
    assert verificar(cliente, login, rid)["resultado"] == "INTEGRA"

    alterar(motor, *tabla_disparador, sentencia, {"id": rid})
    verificacion = verificar(cliente, login, rid)
    niveles = por_nivel(verificacion)
    obtenidas = {n for n, r in niveles.items() if r == "ALTERADA"}
    cumple = verificacion["resultado"] == "ALTERADA" and obtenidas == alteradas
    RESULTADOS.append(
        {
            "tipo": "alteracion",
            "caso": caso,
            "esperado": sorted(alteradas),
            "obtenido": sorted(obtenidas),
            "global": verificacion["resultado"],
            "cumple": cumple,
        }
    )
    assert cumple, (caso, niveles)


def test_sin_falsos_positivos_despues_del_despacho_y_del_acta(cliente, login):
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, 3)
    etapas = {"APROBADA": verificar(cliente, login, rid)}

    from tests.integracion.apoyo import despachar

    assert despachar(cliente, login, rid, {"INT-001": 10, "INT-002": 4}).status_code == 201
    etapas["EN_TRANSITO"] = verificar(cliente, login, rid)
    assert firmar_acta(cliente, login, rid, {"INT-001": 10, "INT-002": 3}).status_code == 201
    etapas["CONFIRMADA"] = verificar(cliente, login, rid)

    for etapa, verificacion in etapas.items():
        niveles = por_nivel(verificacion)
        cumple = verificacion["resultado"] == "INTEGRA" and all(
            niveles[n] == "INTEGRA" for n in NIVELES_PREVIOS
        )
        RESULTADOS.append(
            {
                "tipo": "sin_falso_positivo",
                "caso": etapa,
                "esperado": "INTEGRA",
                "obtenido": niveles,
                "global": verificacion["resultado"],
                "cumple": cumple,
            }
        )
        assert cumple, (etapa, niveles)
    assert "ACTA_RECEPCION" in por_nivel(etapas["CONFIRMADA"])
