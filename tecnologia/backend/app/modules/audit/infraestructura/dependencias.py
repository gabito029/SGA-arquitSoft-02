"""Composición del módulo de auditoría: otros módulos obtienen aquí el registro encadenado, sin
conocer su tabla ni su adaptador."""

from sqlalchemy.orm import Session

from app.modules.audit.dominio.puertos import RegistroAuditoria
from app.modules.audit.infraestructura.registro_encadenado import RegistroAuditoriaEncadenado


def construir_registro_auditoria(sesion: Session) -> RegistroAuditoria:
    return RegistroAuditoriaEncadenado(sesion)
