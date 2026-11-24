"""Casos de uso de lectura: bandeja paginada y detalle con acciones disponibles (FR-002, FR-029).

Arma la *vista* del requerimiento que expone la API (esquema ``Requerimiento`` del contrato):
datos de la entidad más los nombres de la unidad, la Gran Unidad, el almacén y los ítems, que
salen del servicio público del catálogo.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.catalog.dominio.tipos import Categoria
from app.modules.requests.aplicacion.politica_acceso import (
    Accion,
    Actor,
    acciones_disponibles,
    exigir_visible,
    filtro_visibilidad,
)
from app.modules.requests.dominio.estado import EstadoRequerimiento
from app.modules.requests.dominio.puertos import (
    ConsultaCatalogo,
    ItemCatalogo,
    RepositorioRequerimientos,
)
from app.modules.requests.dominio.requerimiento import Requerimiento

TAMANO_MAXIMO_PAGINA = 50


@dataclass(frozen=True)
class Resumen:
    id: uuid.UUID
    codigo: str
    nombre: str


@dataclass(frozen=True)
class VistaItem:
    item: ItemCatalogo
    cantidad_solicitada: int
    cantidad_despachada: int | None
    cantidad_recibida: int | None
    observacion: str | None


@dataclass(frozen=True)
class VistaRequerimiento:
    id: uuid.UUID
    codigo: str
    estado: EstadoRequerimiento
    categoria: Categoria
    unidad: Resumen
    gran_unidad: Resumen | None
    almacen: Resumen | None
    monto_total: Decimal | None
    items: list[VistaItem]
    creado_en: datetime | None
    actualizado_en: datetime | None
    acciones_disponibles: list[Accion]


@dataclass(frozen=True)
class PaginaVistas:
    items: list[VistaRequerimiento]
    total: int
    page: int
    size: int


class ConstructorVistas:
    """Convierte entidades en vistas consultando el catálogo una vez por lote de ítems."""

    def __init__(self, catalogo: ConsultaCatalogo) -> None:
        self._catalogo = catalogo

    def _organo(self, organo_id: uuid.UUID) -> Resumen | None:
        o = self._catalogo.organo(organo_id)
        return Resumen(o.id, o.codigo, o.nombre) if o else None

    def _almacen(self, almacen_id: uuid.UUID) -> Resumen | None:
        a = self._catalogo.almacen(almacen_id)
        return Resumen(a.id, a.codigo, a.nombre) if a else None

    def construir(self, actor: Actor, reqs: list[Requerimiento]) -> list[VistaRequerimiento]:
        items = self._catalogo.items([i.item_id for r in reqs for i in r.items])
        vistas = []
        for r in reqs:
            unidad = self._organo(r.unidad_id) or Resumen(r.unidad_id, "", "")
            vistas.append(
                VistaRequerimiento(
                    id=r.id,
                    codigo=r.codigo,
                    estado=r.estado,
                    categoria=r.categoria,
                    unidad=unidad,
                    gran_unidad=self._organo(r.gran_unidad_id),
                    almacen=self._almacen(r.almacen_id),
                    monto_total=r.monto_total,
                    items=[
                        VistaItem(
                            item=items[i.item_id],
                            cantidad_solicitada=i.cantidad_solicitada,
                            cantidad_despachada=i.cantidad_despachada,
                            cantidad_recibida=i.cantidad_recibida,
                            observacion=i.observacion,
                        )
                        for i in r.items
                        if i.item_id in items
                    ],
                    creado_en=r.creado_en,
                    actualizado_en=r.actualizado_en,
                    acciones_disponibles=acciones_disponibles(actor, r),
                )
            )
        return vistas

    def una(self, actor: Actor, req: Requerimiento) -> VistaRequerimiento:
        return self.construir(actor, [req])[0]


class ConsultarRequerimientos:
    def __init__(self, repositorio: RepositorioRequerimientos, catalogo: ConsultaCatalogo) -> None:
        self._repositorio = repositorio
        self._vistas = ConstructorVistas(catalogo)

    def bandeja(
        self,
        actor: Actor,
        *,
        estado: EstadoRequerimiento | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginaVistas:
        page = max(page, 1)
        size = min(max(size, 1), TAMANO_MAXIMO_PAGINA)
        pagina = self._repositorio.listar_paginado(filtro_visibilidad(actor), estado, page, size)
        return PaginaVistas(
            items=self._vistas.construir(actor, pagina.elementos),
            total=pagina.total,
            page=pagina.page,
            size=pagina.size,
        )

    def detalle(self, actor: Actor, requerimiento_id: uuid.UUID) -> VistaRequerimiento:
        req = self._repositorio.obtener(requerimiento_id)
        rechazado_desde = (
            self._repositorio.estado_previo_al_rechazo(req.id)
            if req is not None and req.estado is EstadoRequerimiento.RECHAZADA
            else None
        )
        return self._vistas.una(actor, exigir_visible(actor, req, rechazado_desde))
