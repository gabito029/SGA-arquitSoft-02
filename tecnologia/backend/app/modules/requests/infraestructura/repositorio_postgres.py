"""Adaptador del repositorio de requerimientos sobre PostgreSQL (patrón Repository, research §5).

Trabaja dentro de la sesión de la Unidad de Trabajo de quien lo llama: no confirma ni deshace.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, and_, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.requests.dominio.estado import AccionHistorial, EstadoRequerimiento
from app.modules.requests.dominio.puertos import (
    EntradaHistorial,
    FiltroVisibilidad,
    Pagina,
    RegistroHistorial,
)
from app.modules.requests.dominio.requerimiento import ItemRequerimiento, Requerimiento
from app.modules.requests.infraestructura.modelos import (
    HistorialRequerimientoModelo,
    ItemRequerimientoModelo,
    RequerimientoModelo,
)

# Clave fija del bloqueo consultivo que serializa la generación de códigos.
CLAVE_BLOQUEO_CODIGO = 488_000_002
PREFIJO_CODIGO = "REQ"

COLUMNAS_JURISDICCION = {
    "unidad_id": RequerimientoModelo.unidad_id,
    "gran_unidad_id": RequerimientoModelo.gran_unidad_id,
    "almacen_id": RequerimientoModelo.almacen_id,
}


def _item(m: ItemRequerimientoModelo) -> ItemRequerimiento:
    return ItemRequerimiento(
        item_id=m.item_id,
        cantidad_solicitada=m.cantidad_solicitada,
        cantidad_despachada=m.cantidad_despachada,
        cantidad_recibida=m.cantidad_recibida,
        observacion=m.observacion,
    )


def _entidad(m: RequerimientoModelo, items: list[ItemRequerimiento]) -> Requerimiento:
    # Los niveles ya firmados los aporta el módulo de firma a partir de la US2.
    return Requerimiento(
        id=m.id,
        codigo=m.codigo,
        unidad_id=m.unidad_id,
        gran_unidad_id=m.gran_unidad_id,
        almacen_id=m.almacen_id,
        categoria=m.categoria,
        creado_por=m.creado_por,
        items=items,
        estado=m.estado,
        monto_total=m.monto_total,
        version=m.version,
        creado_en=m.creado_en,
        actualizado_en=m.actualizado_en,
    )


class RepositorioRequerimientosPostgres:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    # --- Código legible ---

    def siguiente_codigo(self, anio: int) -> str:
        self._sesion.execute(select(func.pg_advisory_xact_lock(CLAVE_BLOQUEO_CODIGO)))
        prefijo = f"{PREFIJO_CODIGO}-{anio:04d}-"
        ultimo = self._sesion.scalar(
            select(func.max(RequerimientoModelo.codigo)).where(
                RequerimientoModelo.codigo.like(f"{prefijo}%")
            )
        )
        numero = int(ultimo.removeprefix(prefijo)) + 1 if ultimo else 1
        return f"{prefijo}{numero:06d}"

    # --- Lectura ---

    def _items_de(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, list[ItemRequerimiento]]:
        por_requerimiento: dict[uuid.UUID, list[ItemRequerimiento]] = {i: [] for i in ids}
        if not ids:
            return por_requerimiento
        consulta = (
            select(ItemRequerimientoModelo)
            .where(ItemRequerimientoModelo.requerimiento_id.in_(ids))
            .order_by(ItemRequerimientoModelo.requerimiento_id, ItemRequerimientoModelo.item_id)
        )
        for m in self._sesion.scalars(consulta):
            por_requerimiento[m.requerimiento_id].append(_item(m))
        return por_requerimiento

    def _cargar(self, consulta: Select) -> Requerimiento | None:
        m = self._sesion.scalar(consulta)
        if m is None:
            return None
        return _entidad(m, self._items_de([m.id])[m.id])

    def obtener(self, requerimiento_id: uuid.UUID) -> Requerimiento | None:
        return self._cargar(
            select(RequerimientoModelo).where(RequerimientoModelo.id == requerimiento_id)
        )

    def obtener_para_actualizar(self, requerimiento_id: uuid.UUID) -> Requerimiento | None:
        return self._cargar(
            select(RequerimientoModelo)
            .where(RequerimientoModelo.id == requerimiento_id)
            .with_for_update()
            # Siempre los datos de la base, no los que la sesión tenga en memoria.
            .execution_options(populate_existing=True)
        )

    def estado_previo_al_rechazo(self, requerimiento_id: uuid.UUID) -> EstadoRequerimiento | None:
        return self._sesion.scalar(
            select(HistorialRequerimientoModelo.estado_anterior)
            .where(
                HistorialRequerimientoModelo.requerimiento_id == requerimiento_id,
                HistorialRequerimientoModelo.accion == AccionHistorial.RECHAZAR,
            )
            .limit(1)
        )

    def listar_paginado(
        self,
        filtro: FiltroVisibilidad,
        estado: EstadoRequerimiento | None,
        page: int,
        size: int,
    ) -> Pagina:
        if filtro.ninguno:
            return Pagina(elementos=[], total=0, page=page, size=size)

        condiciones = []
        if filtro.campo is not None:
            condiciones.append(COLUMNAS_JURISDICCION[filtro.campo] == filtro.valor)
        if not filtro.incluir_borradores:
            condiciones.append(RequerimientoModelo.estado != EstadoRequerimiento.BORRADOR)
        if filtro.estados is not None:
            visibles = RequerimientoModelo.estado.in_(filtro.estados)
            if filtro.rechazados_desde is not None:
                rechazado_aqui = and_(
                    RequerimientoModelo.estado == EstadoRequerimiento.RECHAZADA,
                    exists().where(
                        HistorialRequerimientoModelo.requerimiento_id == RequerimientoModelo.id,
                        HistorialRequerimientoModelo.accion == AccionHistorial.RECHAZAR,
                        HistorialRequerimientoModelo.estado_anterior == filtro.rechazados_desde,
                    ),
                )
                visibles = or_(visibles, rechazado_aqui)
            condiciones.append(visibles)
        if estado is not None:
            condiciones.append(RequerimientoModelo.estado == estado)

        total = self._sesion.scalar(
            select(func.count()).select_from(RequerimientoModelo).where(*condiciones)
        )
        # Recientes primero (índices de bandeja de data-model.md §8).
        modelos = list(
            self._sesion.scalars(
                select(RequerimientoModelo)
                .where(*condiciones)
                .order_by(RequerimientoModelo.creado_en.desc(), RequerimientoModelo.id)
                .offset((page - 1) * size)
                .limit(size)
            )
        )
        items = self._items_de([m.id for m in modelos])
        return Pagina(
            elementos=[_entidad(m, items[m.id]) for m in modelos],
            total=total or 0,
            page=page,
            size=size,
        )

    # --- Escritura ---

    def guardar(self, requerimiento: Requerimiento) -> None:
        """Inserta o actualiza el requerimiento y sus ítems.

        Al actualizar, los ítems se escriben **antes** que el estado: el disparador de la migración
        0002 bloquea los ítems cuando el requerimiento ya está en un estado final, así que el acta
        (EN_TRANSITO → CONFIRMADA) debe registrar lo recibido mientras aún está EN_TRANSITO.
        """
        r = requerimiento
        modelo = self._sesion.get(RequerimientoModelo, r.id)
        if modelo is None:
            modelo = RequerimientoModelo(
                id=r.id,
                codigo=r.codigo,
                unidad_id=r.unidad_id,
                gran_unidad_id=r.gran_unidad_id,
                almacen_id=r.almacen_id,
                categoria=r.categoria,
                creado_por=r.creado_por,
                estado=r.estado,
                monto_total=r.monto_total,
                version=r.version,
            )
            self._sesion.add(modelo)
            self._sesion.flush()
            self._sincronizar_items(r)
        else:
            self._sincronizar_items(r)
            self._sesion.flush()
            modelo.actualizado_en = datetime.now(UTC)
            modelo.estado = r.estado
            modelo.monto_total = r.monto_total
            modelo.version = r.version
        self._sesion.flush()
        self._sesion.refresh(modelo)
        r.creado_en = modelo.creado_en
        r.actualizado_en = modelo.actualizado_en

    def _sincronizar_items(self, r: Requerimiento) -> None:
        existentes = {
            m.item_id: m
            for m in self._sesion.scalars(
                select(ItemRequerimientoModelo).where(
                    ItemRequerimientoModelo.requerimiento_id == r.id
                )
            )
        }
        nuevos = {i.item_id: i for i in r.items}
        for item_id, modelo in existentes.items():
            if item_id not in nuevos:
                self._sesion.delete(modelo)
        for item_id, item in nuevos.items():
            modelo = existentes.get(item_id)
            if modelo is None:
                modelo = ItemRequerimientoModelo(requerimiento_id=r.id, item_id=item_id)
                self._sesion.add(modelo)
            modelo.cantidad_solicitada = item.cantidad_solicitada
            modelo.cantidad_despachada = item.cantidad_despachada
            modelo.cantidad_recibida = item.cantidad_recibida
            modelo.observacion = item.observacion

    def agregar_historial(self, entrada: EntradaHistorial) -> None:
        self._sesion.add(
            HistorialRequerimientoModelo(
                requerimiento_id=entrada.requerimiento_id,
                accion=entrada.accion,
                estado_anterior=entrada.estado_anterior,
                estado_nuevo=entrada.estado_nuevo,
                usuario_id=entrada.usuario_id,
                rol=entrada.rol,
                organo_id=entrada.organo_id,
                motivo=entrada.motivo,
            )
        )
        self._sesion.flush()

    def historial(self, requerimiento_id: uuid.UUID) -> list[RegistroHistorial]:
        return [
            RegistroHistorial(
                accion=m.accion,
                estado_anterior=m.estado_anterior,
                estado_nuevo=m.estado_nuevo,
                usuario_id=m.usuario_id,
                rol=m.rol.value,
                organo_id=m.organo_id,
                motivo=m.motivo,
                ocurrido_en=m.ocurrido_en,
            )
            for m in self._sesion.scalars(
                select(HistorialRequerimientoModelo)
                .where(HistorialRequerimientoModelo.requerimiento_id == requerimiento_id)
                # Varias entradas de una misma transacción comparten la hora: decide el id.
                .order_by(HistorialRequerimientoModelo.ocurrido_en, HistorialRequerimientoModelo.id)
            )
        ]
