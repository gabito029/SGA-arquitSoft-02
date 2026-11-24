"""T032: máquina de estados del requerimiento (data-model.md §6; principio VI).

Cubre cada transición válida, el rechazo de toda transición no listada, la doble firma, el motivo
obligatorio, la anulación solo desde BORRADOR y las cantidades fuera de rango.
"""

import uuid
from decimal import Decimal

import pytest

from app.modules.catalog.dominio.tipos import Categoria
from app.modules.requests.dominio.errores import (
    CantidadInvalida,
    ItemsInvalidos,
    MotivoObligatorio,
    NivelYaFirmado,
    RequiereCologe,
    TransicionNoPermitida,
)
from app.modules.requests.dominio.estado import ESTADOS_FINALES
from app.modules.requests.dominio.estado import EstadoRequerimiento as E
from app.modules.requests.dominio.requerimiento import (
    LineaSolicitud,
    Recepcion,
    Requerimiento,
)
from app.modules.signing.dominio.tipos import NivelFirma as N

ITEM_A = uuid.uuid4()
ITEM_B = uuid.uuid4()
INT = Categoria.INTENDENCIA


def lineas(*pares: tuple[uuid.UUID, int], categoria: Categoria = INT) -> list[LineaSolicitud]:
    return [LineaSolicitud(item_id=i, categoria=categoria, cantidad=c) for i, c in pares]


def nuevo(*pares: tuple[uuid.UUID, int]) -> Requerimiento:
    return Requerimiento.crear(
        id=uuid.uuid4(),
        codigo="REQ-2026-000001",
        unidad_id=uuid.uuid4(),
        gran_unidad_id=uuid.uuid4(),
        almacen_id=uuid.uuid4(),
        categoria=INT,
        creado_por=uuid.uuid4(),
        lineas=lineas(*(pares or ((ITEM_A, 5), (ITEM_B, 3)))),
    )


def enviado() -> Requerimiento:
    req = nuevo()
    req.enviar(monto_total=Decimal("100.00"), requiere_cologe=False)
    return req


def en_estado(estado: E) -> Requerimiento:
    """Lleva un requerimiento nuevo hasta ``estado`` por el camino válido."""
    req = nuevo()
    pasos = {
        E.BORRADOR: [],
        E.PENDIENTE_VB_UNIDAD: ["enviar"],
        E.PENDIENTE_CONFORMIDAD: ["enviar", N.VB_UNIDAD],
        E.PENDIENTE_APROBACION: ["enviar", N.VB_UNIDAD, N.CONFORMIDAD_GU],
        E.APROBADA: ["enviar", N.VB_UNIDAD, N.CONFORMIDAD_GU, N.APROBACION_ALMACEN],
        E.EN_TRANSITO: ["enviar", N.VB_UNIDAD, N.CONFORMIDAD_GU, N.APROBACION_ALMACEN, "despachar"],
        E.CONFIRMADA: [
            "enviar",
            N.VB_UNIDAD,
            N.CONFORMIDAD_GU,
            N.APROBACION_ALMACEN,
            "despachar",
            "acta",
        ],
        E.RECHAZADA: ["enviar", "rechazar"],
        E.ANULADA: ["anular"],
    }[estado]
    for paso in pasos:
        if paso == "enviar":
            req.enviar(monto_total=Decimal("100.00"), requiere_cologe=False)
        elif paso == "despachar":
            req.despachar({ITEM_A: 5, ITEM_B: 3})
        elif paso == "acta":
            req.firmar_acta({ITEM_A: Recepcion(5), ITEM_B: Recepcion(3)})
        elif paso == "rechazar":
            req.rechazar(N.VB_UNIDAD, "No corresponde")
        elif paso == "anular":
            req.anular("Error de registro")
        else:
            req.firmar(paso)
    assert req.estado == estado
    return req


# --- Crear y editar ---


def test_crear_queda_en_borrador_con_version_1():
    req = nuevo()
    assert req.estado == E.BORRADOR
    assert req.version == 1
    assert [i.cantidad_solicitada for i in req.items] == [5, 3]


@pytest.mark.parametrize(
    ("entrada", "error"),
    [
        ([], ItemsInvalidos),
        (lineas((ITEM_A, 1), (ITEM_A, 2)), ItemsInvalidos),
        (
            lineas((ITEM_A, 1)) + lineas((ITEM_B, 1), categoria=Categoria.MATERIAL_GUERRA),
            ItemsInvalidos,
        ),
        (lineas((ITEM_A, 0)), CantidadInvalida),
        (lineas((ITEM_A, -2)), CantidadInvalida),
        ([LineaSolicitud(ITEM_A, INT, True)], CantidadInvalida),  # type: ignore[arg-type]
        ([LineaSolicitud(ITEM_A, INT, 1.5)], CantidadInvalida),  # type: ignore[arg-type]
    ],
    ids=["sin-items", "item-repetido", "categoria-mixta", "cero", "negativa", "bool", "decimal"],
)
def test_crear_valida_items_y_cantidades(entrada, error):
    with pytest.raises(error):
        Requerimiento.crear(
            id=uuid.uuid4(),
            codigo="REQ-2026-000002",
            unidad_id=uuid.uuid4(),
            gran_unidad_id=uuid.uuid4(),
            almacen_id=uuid.uuid4(),
            categoria=INT,
            creado_por=uuid.uuid4(),
            lineas=entrada,
        )


def test_editar_en_borrador_reemplaza_items_y_sube_version():
    req = nuevo()
    req.editar(lineas((ITEM_B, 9)))
    assert req.estado == E.BORRADOR
    assert [(i.item_id, i.cantidad_solicitada) for i in req.items] == [(ITEM_B, 9)]
    assert req.version == 2


def test_editar_valida_igual_que_crear():
    req = nuevo()
    with pytest.raises(CantidadInvalida):
        req.editar(lineas((ITEM_A, 0)))
    with pytest.raises(ItemsInvalidos):
        req.editar(lineas((ITEM_A, 1), categoria=Categoria.MATERIAL_GUERRA))


# --- Enviar (RN03, FR-012) ---


def test_enviar_pasa_a_pendiente_vb_y_fija_monto():
    req = nuevo()
    req.enviar(monto_total=Decimal("250.50"), requiere_cologe=False)
    assert req.estado == E.PENDIENTE_VB_UNIDAD
    assert req.monto_total == Decimal("250.50")
    assert req.version == 2
    assert req.nivel_pendiente == N.VB_UNIDAD


def test_enviar_que_requiere_cologe_queda_bloqueado_sin_cambios():
    req = nuevo()
    with pytest.raises(RequiereCologe) as error:
        req.enviar(monto_total=Decimal("90000"), requiere_cologe=True)
    assert error.value.codigo == "REQUIERE_COLOGE"
    assert "COLOGE" in error.value.mensaje
    assert req.estado == E.BORRADOR
    assert req.version == 1
    assert req.monto_total is None


# --- Conducto regular ---


def test_flujo_completo_por_el_conducto_regular():
    req = enviado()
    req.firmar(N.VB_UNIDAD)
    assert req.estado == E.PENDIENTE_CONFORMIDAD
    req.firmar(N.CONFORMIDAD_GU)
    assert req.estado == E.PENDIENTE_APROBACION
    req.firmar(N.APROBACION_ALMACEN)
    assert req.estado == E.APROBADA
    req.despachar({ITEM_A: 4, ITEM_B: 3})
    assert req.estado == E.EN_TRANSITO
    hubo_diferencias = req.firmar_acta(
        {ITEM_A: Recepcion(3, "  Una ración dañada  "), ITEM_B: Recepcion(3)}
    )
    assert req.estado == E.CONFIRMADA
    assert hubo_diferencias is True
    assert req.items[0].observacion == "Una ración dañada"
    assert req.items[1].observacion is None
    assert req.version == 7
    assert req.es_final
    assert req.niveles_firmados == {
        N.VB_UNIDAD,
        N.CONFORMIDAD_GU,
        N.APROBACION_ALMACEN,
        N.ACTA_RECEPCION,
    }


def test_acta_sin_diferencias():
    req = en_estado(E.EN_TRANSITO)
    assert req.firmar_acta({ITEM_A: Recepcion(5), ITEM_B: Recepcion(3)}) is False


@pytest.mark.parametrize(
    ("estado", "nivel"),
    [
        (E.PENDIENTE_VB_UNIDAD, N.VB_UNIDAD),
        (E.PENDIENTE_CONFORMIDAD, N.CONFORMIDAD_GU),
        (E.PENDIENTE_APROBACION, N.APROBACION_ALMACEN),
    ],
)
def test_cada_nivel_puede_rechazar_con_motivo(estado, nivel):
    req = en_estado(estado)
    req.rechazar(nivel, "Falta sustento")
    assert req.estado == E.RECHAZADA
    assert nivel in req.niveles_firmados


@pytest.mark.parametrize("motivo", ["", "   ", None])
def test_rechazar_sin_motivo_falla_y_no_cambia_nada(motivo):
    req = enviado()
    with pytest.raises(MotivoObligatorio):
        req.rechazar(N.VB_UNIDAD, motivo)  # type: ignore[arg-type]
    assert req.estado == E.PENDIENTE_VB_UNIDAD
    assert req.niveles_firmados == set()


def test_ningun_nivel_se_omite():
    req = enviado()
    with pytest.raises(TransicionNoPermitida):
        req.firmar(N.CONFORMIDAD_GU)  # conformidad antes del visto bueno
    with pytest.raises(TransicionNoPermitida):
        req.firmar(N.APROBACION_ALMACEN)
    assert req.estado == E.PENDIENTE_VB_UNIDAD


def test_un_nivel_no_firma_dos_veces():
    req = enviado()
    req.firmar(N.VB_UNIDAD)
    with pytest.raises(NivelYaFirmado) as error:
        req.firmar(N.VB_UNIDAD)
    assert error.value.codigo == "NIVEL_YA_FIRMADO"
    with pytest.raises(NivelYaFirmado):
        req.rechazar(N.VB_UNIDAD, "Cambio de opinión")


def test_el_acta_no_se_firma_dos_veces():
    req = en_estado(E.CONFIRMADA)
    with pytest.raises(NivelYaFirmado):
        req.firmar_acta({ITEM_A: Recepcion(5), ITEM_B: Recepcion(3)})


# --- Anular (FR-022) ---


def test_anular_desde_borrador_con_motivo():
    req = nuevo()
    req.anular("Se registró por error")
    assert req.estado == E.ANULADA


def test_anular_sin_motivo_falla():
    req = nuevo()
    with pytest.raises(MotivoObligatorio):
        req.anular("  ")
    assert req.estado == E.BORRADOR


@pytest.mark.parametrize("estado", [e for e in E if e not in (E.BORRADOR,)])
def test_solo_se_anula_desde_borrador(estado):
    if estado == E.PENDIENTE_AUTORIZACION_COLOGE:
        req = nuevo()
        req.estado = estado
    else:
        req = en_estado(estado)
    with pytest.raises(TransicionNoPermitida):
        req.anular("Motivo válido")


# --- Despacho y acta: cantidades ---


@pytest.mark.parametrize(
    ("cantidades", "error"),
    [
        ({ITEM_A: 6, ITEM_B: 3}, CantidadInvalida),  # más de lo solicitado
        ({ITEM_A: -1, ITEM_B: 3}, CantidadInvalida),
        ({ITEM_A: 0, ITEM_B: 0}, CantidadInvalida),  # nada que despachar
        ({ITEM_A: 5}, ItemsInvalidos),  # falta un ítem
        ({ITEM_A: 5, ITEM_B: 3, uuid.uuid4(): 1}, ItemsInvalidos),  # ítem ajeno
    ],
    ids=["excede", "negativa", "todo-cero", "falta-item", "item-ajeno"],
)
def test_despacho_con_cantidades_invalidas(cantidades, error):
    req = en_estado(E.APROBADA)
    with pytest.raises(error):
        req.despachar(cantidades)
    assert req.estado == E.APROBADA
    assert all(i.cantidad_despachada is None for i in req.items)


def test_despacho_parcial_registra_lo_despachado():
    req = en_estado(E.APROBADA)
    req.despachar({ITEM_A: 2, ITEM_B: 0})
    assert [i.cantidad_despachada for i in req.items] == [2, 0]


@pytest.mark.parametrize(
    ("recepcion", "error"),
    [
        ({ITEM_A: Recepcion(-1), ITEM_B: Recepcion(3)}, CantidadInvalida),
        ({ITEM_A: Recepcion(5)}, ItemsInvalidos),
    ],
    ids=["negativa", "falta-item"],
)
def test_acta_con_datos_invalidos(recepcion, error):
    req = en_estado(E.EN_TRANSITO)
    with pytest.raises(error):
        req.firmar_acta(recepcion)
    assert req.estado == E.EN_TRANSITO


# --- Toda transición no listada se rechaza ---

ACCIONES = {
    "editar": lambda r: r.editar(lineas((ITEM_A, 1))),
    "enviar": lambda r: r.enviar(monto_total=Decimal("1"), requiere_cologe=False),
    "anular": lambda r: r.anular("Motivo"),
    "firmar_vb": lambda r: r.firmar(N.VB_UNIDAD),
    "firmar_conformidad": lambda r: r.firmar(N.CONFORMIDAD_GU),
    "firmar_aprobacion": lambda r: r.firmar(N.APROBACION_ALMACEN),
    "rechazar_vb": lambda r: r.rechazar(N.VB_UNIDAD, "Motivo"),
    "despachar": lambda r: r.despachar({ITEM_A: 5, ITEM_B: 3}),
    "firmar_acta": lambda r: r.firmar_acta({ITEM_A: Recepcion(5), ITEM_B: Recepcion(3)}),
}

# Transiciones válidas de data-model.md §6 (estado → acciones permitidas).
PERMITIDAS = {
    E.BORRADOR: {"editar", "enviar", "anular"},
    E.PENDIENTE_VB_UNIDAD: {"firmar_vb", "rechazar_vb"},
    E.PENDIENTE_CONFORMIDAD: {"firmar_conformidad"},
    E.PENDIENTE_APROBACION: {"firmar_aprobacion"},
    E.APROBADA: {"despachar"},
    E.EN_TRANSITO: {"firmar_acta"},
}

CASOS_NO_PERMITIDOS = [
    (estado, accion)
    for estado in [e for e in E if e != E.PENDIENTE_AUTORIZACION_COLOGE]
    for accion in ACCIONES
    if accion not in PERMITIDAS.get(estado, set())
]


@pytest.mark.parametrize(("estado", "accion"), CASOS_NO_PERMITIDOS)
def test_toda_transicion_no_listada_se_rechaza(estado, accion):
    req = en_estado(estado)
    version = req.version
    with pytest.raises((TransicionNoPermitida, NivelYaFirmado)):
        ACCIONES[accion](req)
    assert req.estado == estado
    assert req.version == version


def test_los_estados_finales_no_admiten_ninguna_accion():
    for estado in ESTADOS_FINALES:
        assert PERMITIDAS.get(estado) is None


def test_pendiente_cologe_no_admite_acciones_en_001():
    req = nuevo()
    req.estado = E.PENDIENTE_AUTORIZACION_COLOGE
    for accion in ACCIONES.values():
        with pytest.raises(TransicionNoPermitida):
            accion(req)
