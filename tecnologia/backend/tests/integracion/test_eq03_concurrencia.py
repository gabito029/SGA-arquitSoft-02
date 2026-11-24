"""T067 — EQ-03: despachos concurrentes sin sobregiro (US3 escenario 5; ADR-003, research §5).

Dos hilos, cada uno con su propia conexión, despachan 7 y 7 unidades de un ítem con stock 10
(dos solicitudes APROBADAS distintas). Para que choquen de verdad, la prueba retiene el bloqueo de
la fila de stock hasta que las dos transacciones lo estén esperando. Resultado esperado:
exactamente un 201 y un 409 STOCK_INSUFICIENTE, stock final 3 y 0 diferencias entre
``stock.cantidad`` y Σ movimientos por (almacén, ítem). El resumen va a ``evidencias/EQ-03/``.
"""

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from seeds.cargar import id_fijo
from tests.integracion.apoyo import (
    URL,
    crear_aprobada,
    cuerpo,
    diferencias_invariante,
    esperar_bloqueados,
    item,
    stock,
)

EVIDENCIA = Path(__file__).resolve().parents[4] / "evidencias" / "EQ-03" / "resumen-eq03.json"
REPETICIONES = 3


def _una_corrida(cliente, login, motor) -> dict:
    solicitudes = [crear_aprobada(cliente, login, cuerpo(("INT-010", 7))) for _ in range(2)]
    cabeceras = login("almacenero.sinte")
    respuestas: dict[str, object] = {}

    def despachar(rid: str) -> None:
        respuestas[rid] = cliente.post(
            f"{URL}/{rid}/despacho",
            json={"items": [{"item_id": item("INT-010"), "cantidad": 7}]},
            headers=cabeceras,
        )

    inicio = time.perf_counter()
    with motor.connect() as retenedor:
        transaccion = retenedor.begin()
        retenedor.execute(
            text("SELECT cantidad FROM stock WHERE almacen_id = :a AND item_id = :i FOR UPDATE"),
            {"a": id_fijo("almacen", "SINTE"), "i": id_fijo("item", "INT-010")},
        )
        hilos = [threading.Thread(target=despachar, args=(rid,)) for rid in solicitudes]
        for hilo in hilos:
            hilo.start()
        try:
            esperar_bloqueados(motor, 2)
        finally:
            transaccion.commit()
    for hilo in hilos:
        hilo.join(timeout=30)
    duracion = time.perf_counter() - inicio

    codigos = sorted(r.status_code for r in respuestas.values())
    perdedora = next((r for r in respuestas.values() if r.status_code == 409), None)
    with motor.connect() as conexion:
        salidas = conexion.scalar(
            text(
                "SELECT count(*) FROM movimiento WHERE tipo = 'SALIDA_DESPACHO' "
                "AND requerimiento_id IN (:a, :b)"
            ),
            {"a": solicitudes[0], "b": solicitudes[1]},
        )
        estados = sorted(
            conexion.scalars(
                text("SELECT estado::text FROM requerimiento WHERE id IN (:a, :b)"),
                {"a": solicitudes[0], "b": solicitudes[1]},
            )
        )
    return {
        "codigos": codigos,
        "codigo_error": perdedora.json()["codigo"] if perdedora else None,
        "stock_final": stock(motor, "INT-010"),
        "movimientos_salida": salidas,
        "estados": estados,
        "diferencias_invariante": len(diferencias_invariante(motor)),
        "duracion_s": round(duracion, 3),
    }


def test_dos_despachos_simultaneos_no_sobregiran_el_stock(cliente, login, motor):
    corridas = []
    for numero in range(REPETICIONES):
        if numero:
            # Cada corrida vuelve a 10 con una ENTRADA de 7: el invariante se mantiene.
            with motor.begin() as conexion:
                conexion.execute(
                    text(
                        "INSERT INTO movimiento (almacen_id, item_id, tipo, cantidad, usuario_id) "
                        "VALUES (:a, :i, 'ENTRADA', 7, (SELECT id FROM usuario "
                        "WHERE usuario = 'almacenero.sinte'))"
                    ),
                    {"a": id_fijo("almacen", "SINTE"), "i": id_fijo("item", "INT-010")},
                )
                conexion.execute(
                    text(
                        "UPDATE stock SET cantidad = cantidad + 7 "
                        "WHERE almacen_id = :a AND item_id = :i"
                    ),
                    {"a": id_fijo("almacen", "SINTE"), "i": id_fijo("item", "INT-010")},
                )
        corrida = _una_corrida(cliente, login, motor)
        corridas.append(corrida)
        assert corrida["codigos"] == [201, 409], corrida
        assert corrida["codigo_error"] == "STOCK_INSUFICIENTE"
        assert corrida["stock_final"] == 3
        assert corrida["movimientos_salida"] == 1
        assert corrida["estados"] == ["APROBADA", "EN_TRANSITO"]
        assert corrida["diferencias_invariante"] == 0

    EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCIA.write_text(
        json.dumps(
            {
                "escenario": "EQ-03 despachos concurrentes (incremento 001)",
                "generado_en": datetime.now(UTC).isoformat(timespec="seconds"),
                "estimulo": "2 despachos simultáneos de 7 unidades de INT-010 con stock 10",
                "esperado": "un 201, un 409 STOCK_INSUFICIENTE, stock final 3, 0 diferencias",
                "corridas": corridas,
                "cumple": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
