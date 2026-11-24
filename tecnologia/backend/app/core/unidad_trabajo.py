"""Unidad de Trabajo (ADR-003): una transacción por caso de uso.

Estado, firma, movimientos, historial y auditoría se guardan juntos o no se guarda nada::

    with fabrica_uow() as uow:
        repositorio = RepositorioX(uow.sesion)
        ...
    # commit si el bloque terminó bien; rollback ante cualquier excepción
"""

from collections.abc import Callable
from types import TracebackType

from sqlalchemy.orm import Session

from app.core.base_datos import obtener_fabrica_sesiones


class UnidadTrabajo:
    def __init__(self, fabrica_sesiones: Callable[[], Session] | None = None) -> None:
        self._fabrica_sesiones = fabrica_sesiones or obtener_fabrica_sesiones()
        self._sesion: Session | None = None

    @property
    def sesion(self) -> Session:
        if self._sesion is None:
            raise RuntimeError("La Unidad de Trabajo no está abierta")
        return self._sesion

    def __enter__(self) -> "UnidadTrabajo":
        self._sesion = self._fabrica_sesiones()
        return self

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        error: BaseException | None,
        traza: TracebackType | None,
    ) -> None:
        sesion = self.sesion
        try:
            if tipo is None:
                sesion.commit()
            else:
                sesion.rollback()
        finally:
            sesion.close()
            self._sesion = None

    def confirmar(self) -> None:
        """Confirma lo hecho hasta ahora, por ejemplo antes de lanzar un error que no debe
        deshacer un registro (el intento bloqueado de FR-012)."""
        self.sesion.commit()


FabricaUnidadTrabajo = Callable[[], UnidadTrabajo]


def obtener_fabrica_uow() -> FabricaUnidadTrabajo:
    """Dependencia de FastAPI: las pruebas pueden sustituirla con ``dependency_overrides``."""
    return UnidadTrabajo
