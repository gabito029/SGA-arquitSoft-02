"""Política de acceso (T045): visibilidad de data-model.md §7 y acciones disponibles de §6."""

import uuid

import pytest

from app.core.errores import NoEncontrado
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.identity.dominio.rol import Rol
from app.modules.requests.aplicacion.politica_acceso import (
    Accion,
    Actor,
    acciones_disponibles,
    exigir_visible,
    filtro_visibilidad,
    puede_ver,
)
from app.modules.requests.dominio.estado import EstadoRequerimiento as E
from app.modules.requests.dominio.requerimiento import ItemRequerimiento, Requerimiento

UNIDAD, OTRA_UNIDAD = uuid.uuid4(), uuid.uuid4()
GRAN_UNIDAD, OTRA_GU = uuid.uuid4(), uuid.uuid4()
ALMACEN, OTRO_ALMACEN = uuid.uuid4(), uuid.uuid4()


def req(estado: E) -> Requerimiento:
    return Requerimiento(
        id=uuid.uuid4(),
        codigo="REQ-2026-000001",
        unidad_id=UNIDAD,
        gran_unidad_id=GRAN_UNIDAD,
        almacen_id=ALMACEN,
        categoria=Categoria.INTENDENCIA,
        creado_por=uuid.uuid4(),
        items=[ItemRequerimiento(item_id=uuid.uuid4(), cantidad_solicitada=1)],
        estado=estado,
    )


def actor(rol: Rol, organo: uuid.UUID, almacen: uuid.UUID | None = None) -> Actor:
    return Actor(id=uuid.uuid4(), rol=rol, organo_id=organo, almacen_id=almacen)


OFICIAL = actor(Rol.OFICIAL_LOGISTICA, UNIDAD)
CMDTE = actor(Rol.COMANDANTE_UNIDAD, UNIDAD)
JLOG = actor(Rol.JEFE_LOGISTICA_GU, GRAN_UNIDAD)
JALM = actor(Rol.JEFE_ALMACEN, uuid.uuid4(), ALMACEN)
ALMACENERO = actor(Rol.ALMACENERO, uuid.uuid4(), ALMACEN)
AUDITOR = actor(Rol.AUDITOR, uuid.uuid4())


@pytest.mark.parametrize(
    ("quien", "estado", "visible"),
    [
        (OFICIAL, E.BORRADOR, True),
        (actor(Rol.OFICIAL_LOGISTICA, OTRA_UNIDAD), E.BORRADOR, False),
        (CMDTE, E.BORRADOR, False),
        (CMDTE, E.PENDIENTE_VB_UNIDAD, True),
        (actor(Rol.COMANDANTE_UNIDAD, OTRA_UNIDAD), E.PENDIENTE_VB_UNIDAD, False),
        (JLOG, E.PENDIENTE_CONFORMIDAD, True),
        (actor(Rol.JEFE_LOGISTICA_GU, OTRA_GU), E.PENDIENTE_CONFORMIDAD, False),
        (JALM, E.PENDIENTE_CONFORMIDAD, False),
        (JALM, E.PENDIENTE_APROBACION, True),
        (ALMACENERO, E.APROBADA, True),
        (actor(Rol.ALMACENERO, uuid.uuid4(), OTRO_ALMACEN), E.APROBADA, False),
        (actor(Rol.ALMACENERO, uuid.uuid4(), None), E.APROBADA, False),
        (AUDITOR, E.BORRADOR, False),
        (AUDITOR, E.CONFIRMADA, True),
    ],
)
def test_visibilidad_por_rol(quien, estado, visible):
    assert puede_ver(quien, req(estado)) is visible


def test_el_almacen_ve_solo_los_rechazados_en_su_nivel():
    rechazado = req(E.RECHAZADA)
    assert puede_ver(JALM, rechazado, rechazado_desde=E.PENDIENTE_APROBACION)
    assert not puede_ver(JALM, rechazado, rechazado_desde=E.PENDIENTE_VB_UNIDAD)


def test_filtro_de_almacen_sin_almacen_no_ve_nada():
    assert filtro_visibilidad(actor(Rol.JEFE_ALMACEN, uuid.uuid4(), None)).ninguno


def test_exigir_visible_lanza_404():
    with pytest.raises(NoEncontrado):
        exigir_visible(CMDTE, req(E.BORRADOR))
    with pytest.raises(NoEncontrado):
        exigir_visible(OFICIAL, None)


@pytest.mark.parametrize(
    ("quien", "estado", "acciones"),
    [
        (OFICIAL, E.BORRADOR, [Accion.EDITAR, Accion.ENVIAR, Accion.ANULAR]),
        (OFICIAL, E.PENDIENTE_VB_UNIDAD, []),
        (OFICIAL, E.EN_TRANSITO, [Accion.FIRMAR_ACTA]),
        (CMDTE, E.PENDIENTE_VB_UNIDAD, [Accion.FIRMAR, Accion.RECHAZAR]),
        (CMDTE, E.PENDIENTE_CONFORMIDAD, []),
        (JLOG, E.PENDIENTE_CONFORMIDAD, [Accion.FIRMAR, Accion.RECHAZAR]),
        (JALM, E.PENDIENTE_APROBACION, [Accion.FIRMAR, Accion.RECHAZAR]),
        (ALMACENERO, E.APROBADA, [Accion.DESPACHAR]),
        (JALM, E.APROBADA, []),
        (AUDITOR, E.CONFIRMADA, []),
    ],
)
def test_acciones_disponibles(quien, estado, acciones):
    assert acciones_disponibles(quien, req(estado)) == acciones
