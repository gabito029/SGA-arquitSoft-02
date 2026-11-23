"""Entidad Requerimiento con su máquina de estados (patrón State, ADR-007; data-model.md §6).

La entidad decide qué transición es válida: cualquier acción que no esté en la tabla de §6 lanza
``TransicionNoPermitida``, así ningún nivel del conducto regular se omite ni firma dos veces
(RN01, RN02). Es Python puro: no importa FastAPI, SQLAlchemy ni ``cryptography``.

Quién puede actuar (rol, órgano y jurisdicción) lo valida la capa de aplicación; aquí se valida
*qué* se puede hacer en cada estado y con qué datos.
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.modules.catalog.dominio.tipos import Categoria
from app.modules.requests.dominio.errores import (
    CantidadInvalida,
    ItemsInvalidos,
    MotivoObligatorio,
    NivelYaFirmado,
    RequiereCologe,
    TransicionNoPermitida,
)
from app.modules.requests.dominio.estado import ESTADOS_FINALES, EstadoRequerimiento
from app.modules.requests.dominio.firma_nivel import CONDUCTO_REGULAR, nivel_de
from app.modules.signing.dominio.tipos import NivelFirma

# --- Datos de entrada de las transiciones ---


@dataclass(frozen=True)
class LineaSolicitud:
    """Un ítem pedido, con la categoría que tiene en el catálogo."""

    item_id: uuid.UUID
    categoria: Categoria
    cantidad: int


@dataclass(frozen=True)
class Recepcion:
    """Lo recibido de un ítem al firmar el acta."""

    cantidad_recibida: int
    observacion: str | None = None


@dataclass
class ItemRequerimiento:
    item_id: uuid.UUID
    cantidad_solicitada: int
    cantidad_despachada: int | None = None
    cantidad_recibida: int | None = None
    observacion: str | None = None


# --- Validaciones ---


def _es_entero(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_motivo(motivo: str | None) -> str:
    if motivo is None or not motivo.strip():
        raise MotivoObligatorio()
    return motivo.strip()


def _validar_lineas(lineas: list[LineaSolicitud], categoria: Categoria) -> list[ItemRequerimiento]:
    if not lineas:
        raise ItemsInvalidos("La solicitud debe tener al menos un ítem.")
    ids = [linea.item_id for linea in lineas]
    if len(set(ids)) != len(ids):
        raise ItemsInvalidos("La solicitud no puede repetir un ítem.")
    if any(linea.categoria != categoria for linea in lineas):
        raise ItemsInvalidos("Todos los ítems deben ser de la misma categoría.")
    for linea in lineas:
        if not _es_entero(linea.cantidad) or linea.cantidad <= 0:
            raise CantidadInvalida("La cantidad solicitada debe ser un entero mayor que 0.")
    return [ItemRequerimiento(item_id=li.item_id, cantidad_solicitada=li.cantidad) for li in lineas]


def _validar_cobertura(items: list[ItemRequerimiento], ids: set[uuid.UUID]) -> None:
    esperados = {i.item_id for i in items}
    if ids != esperados:
        raise ItemsInvalidos(
            "Debe indicar una cantidad para cada ítem de la solicitud, y solo esos."
        )


# --- Estados (patrón State) ---


class _Estado:
    """Estado base: ninguna acción está permitida salvo que el estado concreto la defina."""

    nombre: EstadoRequerimiento

    def _no_permitida(self, accion: str) -> TransicionNoPermitida:
        return TransicionNoPermitida(
            f"No se puede {accion} un requerimiento en estado {self.nombre.value}."
        )

    def editar(self, req: "Requerimiento", lineas: list[LineaSolicitud]) -> None:
        raise self._no_permitida("editar")

    def enviar(self, req: "Requerimiento", monto_total: Decimal, requiere_cologe: bool) -> None:
        raise self._no_permitida("enviar")

    def anular(self, req: "Requerimiento", motivo: str) -> None:
        raise self._no_permitida("anular")

    def firmar(self, req: "Requerimiento", nivel: NivelFirma) -> None:
        raise self._no_permitida("firmar")

    def rechazar(self, req: "Requerimiento", nivel: NivelFirma, motivo: str) -> None:
        raise self._no_permitida("rechazar")

    def despachar(self, req: "Requerimiento", cantidades: dict[uuid.UUID, int]) -> None:
        raise self._no_permitida("despachar")

    def firmar_acta(self, req: "Requerimiento", recepcion: dict[uuid.UUID, Recepcion]) -> bool:
        raise self._no_permitida("firmar el acta de")


class _Borrador(_Estado):
    nombre = EstadoRequerimiento.BORRADOR

    def editar(self, req: "Requerimiento", lineas: list[LineaSolicitud]) -> None:
        req.items = _validar_lineas(lineas, req.categoria)
        req._avanzar(EstadoRequerimiento.BORRADOR)

    def enviar(self, req: "Requerimiento", monto_total: Decimal, requiere_cologe: bool) -> None:
        if requiere_cologe:
            # FR-012: el envío se bloquea y la solicitud sigue en BORRADOR, sin cambios.
            raise RequiereCologe()
        req.monto_total = monto_total
        req._avanzar(EstadoRequerimiento.PENDIENTE_VB_UNIDAD)

    def anular(self, req: "Requerimiento", motivo: str) -> None:
        _validar_motivo(motivo)
        req._avanzar(EstadoRequerimiento.ANULADA)


class _PendienteFirma(_Estado):
    """Estados del conducto regular que esperan la firma de un nivel."""

    def __init__(self, nombre: EstadoRequerimiento) -> None:
        self.nombre = nombre
        self.nivel, self.siguiente = CONDUCTO_REGULAR[nombre]

    def _validar_nivel(self, nivel: NivelFirma) -> None:
        if nivel != self.nivel:
            raise TransicionNoPermitida(
                f"El requerimiento espera la firma del nivel {self.nivel.value}, "
                f"no la de {nivel.value}."
            )

    def firmar(self, req: "Requerimiento", nivel: NivelFirma) -> None:
        self._validar_nivel(nivel)
        req.niveles_firmados.add(nivel)
        req._avanzar(self.siguiente)

    def rechazar(self, req: "Requerimiento", nivel: NivelFirma, motivo: str) -> None:
        self._validar_nivel(nivel)
        _validar_motivo(motivo)
        req.niveles_firmados.add(nivel)
        req._avanzar(EstadoRequerimiento.RECHAZADA)


class _Aprobada(_Estado):
    nombre = EstadoRequerimiento.APROBADA

    def despachar(self, req: "Requerimiento", cantidades: dict[uuid.UUID, int]) -> None:
        _validar_cobertura(req.items, set(cantidades))
        for item in req.items:
            cantidad = cantidades[item.item_id]
            if not _es_entero(cantidad) or not 0 <= cantidad <= item.cantidad_solicitada:
                raise CantidadInvalida(
                    "La cantidad despachada debe estar entre 0 y la cantidad solicitada."
                )
        if all(c == 0 for c in cantidades.values()):
            raise CantidadInvalida("Debe despachar al menos un ítem con cantidad mayor que 0.")
        for item in req.items:
            item.cantidad_despachada = cantidades[item.item_id]
        req._avanzar(EstadoRequerimiento.EN_TRANSITO)


class _EnTransito(_Estado):
    nombre = EstadoRequerimiento.EN_TRANSITO

    def firmar_acta(self, req: "Requerimiento", recepcion: dict[uuid.UUID, Recepcion]) -> bool:
        _validar_cobertura(req.items, set(recepcion))
        for r in recepcion.values():
            if not _es_entero(r.cantidad_recibida) or r.cantidad_recibida < 0:
                raise CantidadInvalida("La cantidad recibida debe ser un entero mayor o igual a 0.")
        for item in req.items:
            r = recepcion[item.item_id]
            item.cantidad_recibida = r.cantidad_recibida
            item.observacion = (
                r.observacion.strip() if r.observacion and r.observacion.strip() else None
            )
        req.niveles_firmados.add(NivelFirma.ACTA_RECEPCION)
        req._avanzar(EstadoRequerimiento.CONFIRMADA)
        return req.tiene_diferencias


class _Final(_Estado):
    def __init__(self, nombre: EstadoRequerimiento) -> None:
        self.nombre = nombre


_ESTADOS: dict[EstadoRequerimiento, _Estado] = {
    EstadoRequerimiento.BORRADOR: _Borrador(),
    **{estado: _PendienteFirma(estado) for estado in CONDUCTO_REGULAR},
    EstadoRequerimiento.APROBADA: _Aprobada(),
    EstadoRequerimiento.EN_TRANSITO: _EnTransito(),
    **{estado: _Final(estado) for estado in ESTADOS_FINALES},
    # No se alcanza en 001; cualquier acción sobre él se rechaza.
    EstadoRequerimiento.PENDIENTE_AUTORIZACION_COLOGE: _Final(
        EstadoRequerimiento.PENDIENTE_AUTORIZACION_COLOGE
    ),
}


# --- Entidad ---


@dataclass
class Requerimiento:
    id: uuid.UUID
    codigo: str
    unidad_id: uuid.UUID
    gran_unidad_id: uuid.UUID
    almacen_id: uuid.UUID
    categoria: Categoria
    creado_por: uuid.UUID
    items: list[ItemRequerimiento]
    estado: EstadoRequerimiento = EstadoRequerimiento.BORRADOR
    monto_total: Decimal | None = None
    version: int = 1
    niveles_firmados: set[NivelFirma] | None = None

    def __post_init__(self) -> None:
        if self.niveles_firmados is None:
            self.niveles_firmados = set()

    @classmethod
    def crear(
        cls,
        *,
        id: uuid.UUID,
        codigo: str,
        unidad_id: uuid.UUID,
        gran_unidad_id: uuid.UUID,
        almacen_id: uuid.UUID,
        categoria: Categoria,
        creado_por: uuid.UUID,
        lineas: list[LineaSolicitud],
    ) -> "Requerimiento":
        """Registra una solicitud nueva en BORRADOR (≥ 1 ítem, una sola categoría)."""
        return cls(
            id=id,
            codigo=codigo,
            unidad_id=unidad_id,
            gran_unidad_id=gran_unidad_id,
            almacen_id=almacen_id,
            categoria=categoria,
            creado_por=creado_por,
            items=_validar_lineas(lineas, categoria),
        )

    # --- Consultas ---

    @property
    def es_final(self) -> bool:
        return self.estado in ESTADOS_FINALES

    @property
    def nivel_pendiente(self) -> NivelFirma | None:
        return nivel_de(self.estado)

    @property
    def tiene_diferencias(self) -> bool:
        return any(i.cantidad_recibida != i.cantidad_despachada for i in self.items)

    # --- Transiciones (data-model.md §6) ---

    def editar(self, lineas: list[LineaSolicitud]) -> None:
        self._estado_actual().editar(self, lineas)

    def enviar(self, *, monto_total: Decimal, requiere_cologe: bool) -> None:
        self._estado_actual().enviar(self, monto_total, requiere_cologe)

    def anular(self, motivo: str) -> None:
        self._estado_actual().anular(self, motivo)

    def firmar(self, nivel: NivelFirma) -> None:
        self._verificar_no_firmado(nivel)
        self._estado_actual().firmar(self, nivel)

    def rechazar(self, nivel: NivelFirma, motivo: str) -> None:
        self._verificar_no_firmado(nivel)
        self._estado_actual().rechazar(self, nivel, motivo)

    def despachar(self, cantidades: dict[uuid.UUID, int]) -> None:
        self._estado_actual().despachar(self, cantidades)

    def firmar_acta(self, recepcion: dict[uuid.UUID, Recepcion]) -> bool:
        """Registra lo recibido, pasa a CONFIRMADA y devuelve si hubo diferencias."""
        self._verificar_no_firmado(NivelFirma.ACTA_RECEPCION)
        return self._estado_actual().firmar_acta(self, recepcion)

    # --- Internos ---

    def _estado_actual(self) -> _Estado:
        return _ESTADOS[self.estado]

    def _verificar_no_firmado(self, nivel: NivelFirma) -> None:
        assert self.niveles_firmados is not None
        if nivel in self.niveles_firmados:
            raise NivelYaFirmado()

    def _avanzar(self, nuevo: EstadoRequerimiento) -> None:
        self.estado = nuevo
        self.version += 1
