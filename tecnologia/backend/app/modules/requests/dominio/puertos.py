"""Puertos del módulo de requerimientos (inversión de dependencias, segregación de interfaces).

Los casos de uso dependen de estas interfaces; los adaptadores viven en ``infraestructura/``.
Python puro: no importa FastAPI ni SQLAlchemy.
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.modules.audit.dominio.puertos import RegistroAuditoria
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.requests.dominio.estado import AccionHistorial, EstadoRequerimiento
from app.modules.requests.dominio.requerimiento import Requerimiento
from app.modules.signing.dominio.contenido_canonico import DocumentoFirmable, Firmante
from app.modules.signing.dominio.puertos import FirmaRegistrada
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma

__all__ = [
    "AlmacenResumen",
    "ConsultaCatalogo",
    "ConsultaUsuarios",
    "EntradaHistorial",
    "FiltroVisibilidad",
    "FirmasRequerimiento",
    "ItemCatalogo",
    "OrganoCatalogo",
    "Pagina",
    "RegistroAuditoria",
    "RepositorioRequerimientos",
    "Transaccion",
]


# --- Datos que cruzan los puertos ---


@dataclass(frozen=True)
class EntradaHistorial:
    """Una entrada de la línea de tiempo (data-model.md historial_requerimiento)."""

    requerimiento_id: uuid.UUID
    accion: AccionHistorial
    estado_anterior: EstadoRequerimiento | None
    estado_nuevo: EstadoRequerimiento
    usuario_id: uuid.UUID
    rol: str
    organo_id: uuid.UUID
    motivo: str | None = None


@dataclass(frozen=True)
class FiltroVisibilidad:
    """Qué requerimientos ve un usuario (data-model.md §7), expresado sin SQL.

    - ``campo``/``valor``: columna de jurisdicción (``unidad_id``, ``gran_unidad_id`` o
      ``almacen_id``) y su valor; ``campo`` None significa "todas las jurisdicciones".
    - ``incluir_borradores``: solo los oficiales de logística ven los BORRADOR de su unidad.
    - ``estados``: si no es None, solo esos estados…
    - ``rechazados_desde``: …más los RECHAZADA cuyo rechazo ocurrió en este estado.
    - ``ninguno``: el usuario no ve nada (por ejemplo, un rol de almacén sin almacén).
    """

    campo: str | None
    valor: uuid.UUID | None
    incluir_borradores: bool
    estados: frozenset[EstadoRequerimiento] | None = None
    rechazados_desde: EstadoRequerimiento | None = None
    ninguno: bool = False


@dataclass(frozen=True)
class Pagina:
    elementos: list[Requerimiento]
    total: int
    page: int
    size: int


@dataclass(frozen=True)
class ItemCatalogo:
    id: uuid.UUID
    codigo: str
    nombre: str
    categoria: Categoria
    unidad_medida: str
    valor_unitario: Decimal
    activo: bool


@dataclass(frozen=True)
class OrganoCatalogo:
    id: uuid.UUID
    codigo: str
    nombre: str
    tipo: str
    padre_id: uuid.UUID | None


@dataclass(frozen=True)
class AlmacenResumen:
    id: uuid.UUID
    codigo: str  # el del órgano de servicio al que pertenece (p. ej. SINTE)
    nombre: str


# --- Puertos ---


class RepositorioRequerimientos(Protocol):
    def siguiente_codigo(self, anio: int) -> str:
        """Siguiente ``REQ-AAAA-NNNNNN`` del año, sin colisiones entre transacciones."""
        ...

    def obtener(self, requerimiento_id: uuid.UUID) -> Requerimiento | None: ...

    def obtener_para_actualizar(self, requerimiento_id: uuid.UUID) -> Requerimiento | None:
        """Carga y bloquea la fila (``SELECT … FOR UPDATE``) hasta el fin de la transacción."""
        ...

    def guardar(self, requerimiento: Requerimiento) -> None: ...

    def agregar_historial(self, entrada: EntradaHistorial) -> None: ...

    def estado_previo_al_rechazo(self, requerimiento_id: uuid.UUID) -> EstadoRequerimiento | None:
        """Estado en el que se rechazó el requerimiento, o None si no fue rechazado."""
        ...

    def listar_paginado(
        self,
        filtro: FiltroVisibilidad,
        estado: EstadoRequerimiento | None,
        page: int,
        size: int,
    ) -> Pagina: ...


class ConsultaCatalogo(Protocol):
    """Lo que ``requests`` necesita del catálogo; lo provee el servicio público de ``catalog``."""

    def items(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, ItemCatalogo]: ...

    def organo(self, organo_id: uuid.UUID) -> OrganoCatalogo | None: ...

    def almacen_por_categoria(self, categoria: Categoria) -> uuid.UUID | None: ...

    def almacen(self, almacen_id: uuid.UUID) -> AlmacenResumen | None: ...


class FirmasRequerimiento(Protocol):
    """Lo que ``requests`` necesita del servicio público de ``signing``."""

    def firmar_nivel(
        self,
        documento: DocumentoFirmable,
        nivel: NivelFirma,
        decision: DecisionFirma,
        firmante: Firmante,
    ) -> FirmaRegistrada: ...

    def firmas(self, requerimiento_id: uuid.UUID) -> list[FirmaRegistrada]: ...

    def niveles_firmados(self, requerimiento_id: uuid.UUID) -> set[NivelFirma]: ...


class ConsultaUsuarios(Protocol):
    """Nombres completos de los usuarios; los provee el servicio público de ``identity``."""

    def nombres(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, str]: ...


class Transaccion(Protocol):
    def confirmar(self) -> None:
        """Confirma lo hecho hasta ahora (el intento bloqueado de FR-012 debe quedar)."""
        ...
