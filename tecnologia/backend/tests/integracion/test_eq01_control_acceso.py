"""T057 — EQ-01: control de acceso por rol y jurisdicción (FR-002, FR-003; data-model.md §7).

Matriz parametrizada sobre una solicitud de intendencia de BIM-11 (1.ª DE, almacén SINTE):

- Cada usuario intenta cada acción del conducto regular (enviar, firmar o rechazar) en cada
  estado. Solo el actor que corresponde lo logra; el resto recibe 403 (rol sin permiso), 404 (fuera
  de su jurisdicción o aún no visible para su rol) o 409 (no corresponde al estado actual), y la
  solicitud no cambia.
- Sin token responde 401.
- Fuera de la jurisdicción, consultar responde 404.
- Un BORRADOR solo lo ven los oficiales de logística de su unidad.
- Un usuario sin unidad o sin jurisdicción ve una bandeja vacía y recibe 404.

Debe cumplirse en el 100 % de los casos. El resumen se guarda en ``evidencias/EQ-01/``.
"""

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text

from seeds.cargar import id_fijo
from tests.integracion.apoyo import INTENDENCIA, URL, avanzar, crear_enviada

RAIZ_REPO = Path(__file__).resolve().parents[4]
EVIDENCIA = RAIZ_REPO / "evidencias" / "EQ-01" / "resumen-eq01.json"

# Usuarios de la jurisdicción de la solicitud y de fuera de ella.
PROPIOS = ["oficial.bim11", "cmdte.bim11", "jlog.1de", "jalm.sinte", "almacenero.sinte", "auditor"]
AJENOS = ["oficial.bim21", "cmdte.bim12", "cmdte.bim21", "jlog.2de", "jalm.smge", "almacenero.smge"]
USUARIOS = PROPIOS + AJENOS

# Estado inicial → cuántos niveles del conducto regular se aprueban para llegar a él.
ESTADOS: dict[str, int | None] = {
    "BORRADOR": None,
    "PENDIENTE_VB_UNIDAD": 0,
    "PENDIENTE_CONFORMIDAD": 1,
    "PENDIENTE_APROBACION": 2,
}

MOTIVO = "Motivo de prueba EQ-01"
Accion = Callable[[object, str, dict], object]
ACCIONES: dict[str, Accion] = {
    "ENVIAR": lambda c, rid, h: c.post(f"{URL}/{rid}/enviar", headers=h),
    "FIRMAR": lambda c, rid, h: c.post(
        f"{URL}/{rid}/firmas", json={"decision": "APROBAR"}, headers=h
    ),
    "RECHAZAR": lambda c, rid, h: c.post(
        f"{URL}/{rid}/firmas", json={"decision": "RECHAZAR", "motivo": MOTIVO}, headers=h
    ),
}

# Los únicos (estado, acción, usuario) permitidos; todo lo demás debe denegarse.
PERMITIDOS = {
    ("BORRADOR", "ENVIAR", "oficial.bim11"),
    ("PENDIENTE_VB_UNIDAD", "FIRMAR", "cmdte.bim11"),
    ("PENDIENTE_VB_UNIDAD", "RECHAZAR", "cmdte.bim11"),
    ("PENDIENTE_CONFORMIDAD", "FIRMAR", "jlog.1de"),
    ("PENDIENTE_CONFORMIDAD", "RECHAZAR", "jlog.1de"),
    ("PENDIENTE_APROBACION", "FIRMAR", "jalm.sinte"),
    ("PENDIENTE_APROBACION", "RECHAZAR", "jalm.sinte"),
}

# Roles que el endpoint admite (los demás reciben 403 antes de mirar la solicitud).
ROLES_ENDPOINT = {
    "ENVIAR": {"oficial"},
    "FIRMAR": {"cmdte", "jlog", "jalm"},
    "RECHAZAR": {"cmdte", "jlog", "jalm"},
}

RESULTADOS: list[dict] = []


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
                "escenario": "EQ-01 control de acceso (incremento 001)",
                "generado_en": datetime.now(UTC).isoformat(timespec="seconds"),
                "casos": len(RESULTADOS),
                "cumplidos": cumplidos,
                "porcentaje": round(100 * cumplidos / len(RESULTADOS), 2),
                "por_tipo": {
                    tipo: sum(1 for r in RESULTADOS if r["tipo"] == tipo)
                    for tipo in sorted({r["tipo"] for r in RESULTADOS})
                },
                "fallidos": [r for r in RESULTADOS if not r["cumple"]],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def registrar(tipo: str, caso: str, esperado: object, obtenido: int, cumple: bool) -> None:
    RESULTADOS.append(
        {"tipo": tipo, "caso": caso, "esperado": esperado, "obtenido": obtenido, "cumple": cumple}
    )
    assert cumple, f"{caso}: se esperaba {esperado} y se obtuvo {obtenido}"


def preparar(cliente, login, estado: str) -> str:
    niveles = ESTADOS[estado]
    if niveles is None:
        creado = cliente.post(URL, json=INTENDENCIA, headers=login("oficial.bim11"))
        assert creado.status_code == 201, creado.text
        return creado.json()["id"]
    rid = crear_enviada(cliente, login)
    avanzar(cliente, login, rid, niveles)
    return rid


def estado_actual(motor, rid: str) -> tuple[str, int]:
    with motor.connect() as conexion:
        fila = conexion.execute(
            text("SELECT estado, version FROM requerimiento WHERE id = :id"), {"id": rid}
        ).one()
    return fila.estado, fila.version


CASOS_DENEGADOS = [
    (estado, accion, usuario)
    for estado in ESTADOS
    for accion in ACCIONES
    for usuario in USUARIOS
    if (estado, accion, usuario) not in PERMITIDOS
]


@pytest.mark.parametrize(("estado", "accion", "usuario"), CASOS_DENEGADOS)
def test_accion_que_no_le_corresponde_se_deniega(cliente, login, motor, estado, accion, usuario):
    rid = preparar(cliente, login, estado)
    antes = estado_actual(motor, rid)
    respuesta = ACCIONES[accion](cliente, rid, login(usuario))

    rol_admitido = usuario.split(".")[0] in ROLES_ENDPOINT[accion]
    if not rol_admitido:
        esperado: object = 403
        cumple = respuesta.status_code == 403
    elif usuario in AJENOS:
        esperado = 404
        cumple = respuesta.status_code == 404
    else:
        esperado = [404, 409]
        cumple = respuesta.status_code in (404, 409)
    cumple = cumple and estado_actual(motor, rid) == antes
    registrar(
        "accion_denegada", f"{estado}/{accion}/{usuario}", esperado, respuesta.status_code, cumple
    )


@pytest.mark.parametrize(("estado", "accion", "usuario"), sorted(PERMITIDOS))
def test_solo_el_actor_que_corresponde_lo_logra(cliente, login, estado, accion, usuario):
    rid = preparar(cliente, login, estado)
    respuesta = ACCIONES[accion](cliente, rid, login(usuario))
    esperado = 200 if accion == "ENVIAR" else 201
    registrar(
        "accion_permitida",
        f"{estado}/{accion}/{usuario}",
        esperado,
        respuesta.status_code,
        respuesta.status_code == esperado,
    )


@pytest.mark.parametrize("accion", list(ACCIONES))
def test_sin_token_responde_401(cliente, login, accion):
    rid = preparar(cliente, login, "PENDIENTE_VB_UNIDAD")
    respuesta = ACCIONES[accion](cliente, rid, {})
    registrar("sin_token", accion, 401, respuesta.status_code, respuesta.status_code == 401)


@pytest.mark.parametrize("recurso", ["", "/firmas"])
def test_consultar_sin_token_responde_401(cliente, login, recurso):
    rid = preparar(cliente, login, "PENDIENTE_VB_UNIDAD")
    respuesta = cliente.get(f"{URL}/{rid}{recurso}")
    registrar(
        "sin_token", f"GET{recurso}", 401, respuesta.status_code, respuesta.status_code == 401
    )


@pytest.mark.parametrize("estado", list(ESTADOS))
@pytest.mark.parametrize("usuario", AJENOS)
def test_fuera_de_su_jurisdiccion_consultar_responde_404(cliente, login, estado, usuario):
    rid = preparar(cliente, login, estado)
    cabeceras = login(usuario)
    for recurso in ("", "/firmas"):
        respuesta = cliente.get(f"{URL}/{rid}{recurso}", headers=cabeceras)
        registrar(
            "consulta_ajena",
            f"{estado}/GET{recurso}/{usuario}",
            404,
            respuesta.status_code,
            respuesta.status_code == 404,
        )
    bandeja = cliente.get(URL, headers=cabeceras).json()
    registrar(
        "bandeja_ajena",
        f"{estado}/bandeja/{usuario}",
        "sin la solicitud",
        200,
        rid not in {r["id"] for r in bandeja["items"]},
    )


@pytest.mark.parametrize("usuario", ["cmdte.bim11", "jlog.1de", "jalm.sinte", "auditor"])
def test_un_borrador_solo_lo_ve_su_oficial_de_logistica(cliente, login, usuario):
    rid = preparar(cliente, login, "BORRADOR")
    respuesta = cliente.get(f"{URL}/{rid}", headers=login(usuario))
    registrar(
        "borrador",
        f"BORRADOR/GET/{usuario}",
        404,
        respuesta.status_code,
        respuesta.status_code == 404,
    )


def test_el_oficial_de_la_unidad_si_ve_su_borrador(cliente, login):
    rid = preparar(cliente, login, "BORRADOR")
    respuesta = cliente.get(f"{URL}/{rid}", headers=login("oficial.bim11"))
    registrar(
        "borrador",
        "BORRADOR/GET/oficial.bim11",
        200,
        respuesta.status_code,
        respuesta.status_code == 200,
    )


# --- Usuarios sin unidad o sin jurisdicción (caso límite de spec.md) ---

SIN_JURISDICCION = [
    # Un comandante cuyo órgano es una División, no una UNIDAD.
    ("cmdte.sin.unidad", "COMANDANTE_UNIDAD", "1DE"),
    # Un oficial de logística asignado a una División: no tiene unidad.
    ("oficial.sin.unidad", "OFICIAL_LOGISTICA", "1DE"),
    # Un jefe de logística asignado a una unidad: no tiene Gran Unidad a su cargo.
    ("jlog.sin.gu", "JEFE_LOGISTICA_GU", "BIM-11"),
]


@pytest.fixture
def usuarios_sin_jurisdiccion(motor):
    with motor.begin() as conexion:
        for usuario, rol, organo in SIN_JURISDICCION:
            conexion.execute(
                text(
                    "INSERT INTO usuario (id, usuario, nombre_completo, hash_contrasena, rol, "
                    "organo_id) SELECT :id, :u, :n, hash_contrasena, CAST(:r AS rol), :o "
                    "FROM usuario "
                    "WHERE usuario = 'oficial.bim11' ON CONFLICT (usuario) DO NOTHING"
                ),
                {
                    "id": uuid.uuid4(),
                    "u": usuario,
                    "n": f"Prueba {usuario}",
                    "r": rol,
                    "o": id_fijo("organo", organo),
                },
            )
    return [u for u, _, _ in SIN_JURISDICCION]


@pytest.mark.parametrize("estado", ["PENDIENTE_VB_UNIDAD", "PENDIENTE_CONFORMIDAD"])
def test_usuario_sin_jurisdiccion_no_ve_ni_actua(cliente, login, usuarios_sin_jurisdiccion, estado):
    rid = preparar(cliente, login, estado)
    for usuario in usuarios_sin_jurisdiccion:
        cabeceras = login(usuario)
        bandeja = cliente.get(URL, headers=cabeceras).json()
        registrar(
            "sin_jurisdiccion",
            f"{estado}/bandeja/{usuario}",
            0,
            bandeja["total"],
            bandeja["total"] == 0,
        )
        detalle = cliente.get(f"{URL}/{rid}", headers=cabeceras)
        registrar(
            "sin_jurisdiccion",
            f"{estado}/GET/{usuario}",
            404,
            detalle.status_code,
            detalle.status_code == 404,
        )
    for usuario in ("cmdte.sin.unidad", "jlog.sin.gu"):
        respuesta = ACCIONES["FIRMAR"](cliente, rid, login(usuario))
        registrar(
            "sin_jurisdiccion",
            f"{estado}/FIRMAR/{usuario}",
            404,
            respuesta.status_code,
            respuesta.status_code == 404,
        )
    respuesta = cliente.post(URL, json=INTENDENCIA, headers=login("oficial.sin.unidad"))
    registrar(
        "sin_jurisdiccion",
        "registrar/oficial.sin.unidad",
        403,
        respuesta.status_code,
        respuesta.status_code == 403,
    )
