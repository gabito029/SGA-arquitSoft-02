"""Puerto de la auditoría: cualquier módulo registra eventos sin conocer la tabla."""

from typing import Protocol

from app.modules.audit.dominio.cadena import EventoAuditoria


class RegistroAuditoria(Protocol):
    def registrar(self, evento: EventoAuditoria) -> str:
        """Registra el evento dentro de la transacción en curso y devuelve su huella."""
        ...
