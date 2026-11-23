"""Reglas de la auditoría encadenada (ADR-005, research §6). Python puro.

Cada registro guarda la huella del anterior:
``huella = SHA-256(huella_anterior + JSON canónico del registro)``. Si alguien altera o borra un
registro, la cadena deja de cuadrar desde ese punto (la verificación completa es HU12, en 002).
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.json_canonico import a_json_canonico

HUELLA_INICIAL = "0" * 64


@dataclass(frozen=True)
class EventoAuditoria:
    tipo_evento: str  # p. ej. REQUERIMIENTO.FIRMAR, INVENTARIO.DESPACHO
    entidad: str
    entidad_id: uuid.UUID | None
    usuario_id: uuid.UUID | None
    rol: str | None
    organo_id: uuid.UUID | None
    datos: dict[str, Any] = field(default_factory=dict)


def contenido_registro(evento: EventoAuditoria, ocurrido_en: datetime) -> dict[str, Any]:
    """Campos del registro que entran en la huella."""
    return {
        "tipo_evento": evento.tipo_evento,
        "entidad": evento.entidad,
        "entidad_id": evento.entidad_id,
        "usuario_id": evento.usuario_id,
        "rol": evento.rol,
        "organo_id": evento.organo_id,
        "datos": evento.datos,
        "ocurrido_en": ocurrido_en,
    }


def calcular_huella(huella_anterior: str, contenido: dict[str, Any]) -> str:
    return hashlib.sha256(huella_anterior.encode("ascii") + a_json_canonico(contenido)).hexdigest()
