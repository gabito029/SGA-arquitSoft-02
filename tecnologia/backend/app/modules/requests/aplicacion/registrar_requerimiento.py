"""Casos de uso: registrar un requerimiento en BORRADOR y editarlo (HU02, RF02; FR-005 a FR-008).

- La unidad es la del oficial; la Gran Unidad, el padre de esa unidad; y el almacén, el de la
  categoría de los ítems (FR-006, FR-007).
- Cada ítem debe existir, estar activo y ser de la misma categoría que los demás.
- Se registra ``CREAR`` en el historial y el evento en la auditoría encadenada, todo en la misma
  Unidad de Trabajo que abre quien llama (ADR-003).
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.errores import DetalleError, SinPermiso
from app.modules.audit.dominio.cadena import EventoAuditoria
from app.modules.catalog.dominio.tipos import Categoria, TipoOrgano
from app.modules.requests.aplicacion.politica_acceso import Actor, exigir_visible
from app.modules.requests.dominio.errores import ItemsInvalidos
from app.modules.requests.dominio.estado import AccionHistorial, EstadoRequerimiento
from app.modules.requests.dominio.puertos import (
    ConsultaCatalogo,
    EntradaHistorial,
    RegistroAuditoria,
    RepositorioRequerimientos,
)
from app.modules.requests.dominio.requerimiento import LineaSolicitud, Requerimiento


@dataclass(frozen=True)
class LineaEntrada:
    item_id: uuid.UUID
    cantidad: int


def construir_lineas(
    catalogo: ConsultaCatalogo, lineas: list[LineaEntrada]
) -> tuple[Categoria, list[LineaSolicitud]]:
    """Valida los ítems contra el catálogo y devuelve la categoría común y las líneas.

    Los errores indican el campo (``items.N.item_id``) y el motivo (escenario 3 de la US1).
    """
    if not lineas:
        raise ItemsInvalidos(
            "La solicitud debe tener al menos un ítem.",
            detalles=[DetalleError("items", "Agregue al menos un ítem.")],
        )
    items = catalogo.items([li.item_id for li in lineas])
    detalles: list[DetalleError] = []
    vistos: set[uuid.UUID] = set()
    for indice, linea in enumerate(lineas):
        campo = f"items.{indice}.item_id"
        item = items.get(linea.item_id)
        if item is None:
            detalles.append(DetalleError(campo, "El ítem no existe en el catálogo."))
        elif not item.activo:
            detalles.append(DetalleError(campo, "El ítem está inactivo en el catálogo."))
        if linea.item_id in vistos:
            detalles.append(DetalleError(campo, "El ítem está repetido en la solicitud."))
        vistos.add(linea.item_id)
    if detalles:
        raise ItemsInvalidos(detalles=detalles)

    categorias = {items[li.item_id].categoria for li in lineas}
    if len(categorias) != 1:
        raise ItemsInvalidos(
            "Todos los ítems deben ser de la misma categoría.",
            detalles=[
                DetalleError("items", "Mezcla intendencia y material de guerra en una solicitud.")
            ],
        )
    categoria = categorias.pop()
    return categoria, [
        LineaSolicitud(item_id=li.item_id, categoria=categoria, cantidad=li.cantidad)
        for li in lineas
    ]


def entrada_historial(
    req: Requerimiento,
    actor: Actor,
    accion: AccionHistorial,
    estado_anterior: EstadoRequerimiento | None,
    motivo: str | None = None,
) -> EntradaHistorial:
    return EntradaHistorial(
        requerimiento_id=req.id,
        accion=accion,
        estado_anterior=estado_anterior,
        estado_nuevo=req.estado,
        usuario_id=actor.id,
        rol=actor.rol,
        organo_id=actor.organo_id,
        motivo=motivo,
    )


def evento(req: Requerimiento, actor: Actor, tipo: str, **datos: object) -> EventoAuditoria:
    return EventoAuditoria(
        tipo_evento=tipo,
        entidad="requerimiento",
        entidad_id=req.id,
        usuario_id=actor.id,
        rol=actor.rol,
        organo_id=actor.organo_id,
        datos={"codigo": req.codigo, "estado": req.estado.value, **datos},
    )


def _resumen_items(req: Requerimiento) -> list[dict[str, object]]:
    return [
        {"item_id": str(i.item_id), "cantidad": i.cantidad_solicitada}
        for i in sorted(req.items, key=lambda i: str(i.item_id))
    ]


class RegistrarRequerimiento:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        catalogo: ConsultaCatalogo,
        auditoria: RegistroAuditoria,
        reloj: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repositorio = repositorio
        self._catalogo = catalogo
        self._auditoria = auditoria
        self._reloj = reloj

    def registrar(self, actor: Actor, lineas: list[LineaEntrada]) -> Requerimiento:
        unidad = self._catalogo.organo(actor.organo_id)
        gran_unidad_id = unidad.padre_id if unidad else None
        if unidad is None or unidad.tipo != TipoOrgano.UNIDAD or gran_unidad_id is None:
            # Caso límite de spec.md: un usuario sin unidad o sin jurisdicción no opera.
            raise SinPermiso("Su usuario no está asociado a una unidad con División/Brigada.")

        categoria, lineas_validas = construir_lineas(self._catalogo, lineas)
        almacen_id = self._catalogo.almacen_por_categoria(categoria)
        if almacen_id is None:
            raise ItemsInvalidos(
                "No hay un almacén que atienda esta categoría.",
                detalles=[DetalleError("items", "Ningún almacén atiende esta categoría.")],
            )

        req = Requerimiento.crear(
            id=uuid.uuid4(),
            codigo=self._repositorio.siguiente_codigo(self._reloj().year),
            unidad_id=unidad.id,
            gran_unidad_id=gran_unidad_id,
            almacen_id=almacen_id,
            categoria=categoria,
            creado_por=actor.id,
            lineas=lineas_validas,
        )
        self._repositorio.guardar(req)
        self._repositorio.agregar_historial(
            entrada_historial(req, actor, AccionHistorial.CREAR, None)
        )
        self._auditoria.registrar(
            evento(
                req,
                actor,
                "REQUERIMIENTO.CREAR",
                categoria=categoria.value,
                items=_resumen_items(req),
            )
        )
        return req

    def editar(
        self, actor: Actor, requerimiento_id: uuid.UUID, lineas: list[LineaEntrada]
    ) -> Requerimiento:
        req = exigir_visible(actor, self._repositorio.obtener_para_actualizar(requerimiento_id))
        if req.estado is not EstadoRequerimiento.BORRADOR:
            # FR-008: al enviarla deja de ser editable. La entidad lanza TransicionNoPermitida.
            req.editar([])
        categoria, lineas_validas = construir_lineas(self._catalogo, lineas)
        if categoria != req.categoria:
            raise ItemsInvalidos(
                "La categoría de la solicitud no se puede cambiar.",
                detalles=[
                    DetalleError(
                        "items", f"Los ítems deben ser de la categoría {req.categoria.value}."
                    )
                ],
            )
        req.editar(lineas_validas)
        self._repositorio.guardar(req)
        self._auditoria.registrar(
            evento(req, actor, "REQUERIMIENTO.EDITAR", items=_resumen_items(req))
        )
        return req
