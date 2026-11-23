"""Adaptador de la auditoría encadenada sobre PostgreSQL (research §6, RN07).

Se escribe en la transacción de quien lo llama: si la operación falla, el registro tampoco queda.
Para encadenar sin carreras se toma un ``pg_advisory_xact_lock`` fijo antes de leer el último
registro; el bloqueo se libera solo al terminar la transacción.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.audit.dominio.cadena import (
    HUELLA_INICIAL,
    EventoAuditoria,
    calcular_huella,
    contenido_registro,
)
from app.modules.audit.infraestructura.modelos import RegistroAuditoriaModelo

# Clave arbitraria pero fija del bloqueo consultivo de la cadena de auditoría.
CLAVE_BLOQUEO_CADENA = 488_000_001


class RegistroAuditoriaEncadenado:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def registrar(self, evento: EventoAuditoria) -> str:
        self._sesion.execute(select(func.pg_advisory_xact_lock(CLAVE_BLOQUEO_CADENA)))
        anterior = self._sesion.scalar(
            select(RegistroAuditoriaModelo.huella)
            .order_by(RegistroAuditoriaModelo.id.desc())
            .limit(1)
        )
        huella_anterior = anterior or HUELLA_INICIAL
        # Precisión de microsegundos, la misma que guarda PostgreSQL: la huella se puede recalcular.
        ocurrido_en = datetime.now(UTC)
        huella = calcular_huella(huella_anterior, contenido_registro(evento, ocurrido_en))
        self._sesion.add(
            RegistroAuditoriaModelo(
                tipo_evento=evento.tipo_evento,
                entidad=evento.entidad,
                entidad_id=evento.entidad_id,
                usuario_id=evento.usuario_id,
                rol=evento.rol,
                organo_id=evento.organo_id,
                datos=evento.datos,
                huella_anterior=huella_anterior,
                huella=huella,
                ocurrido_en=ocurrido_en,
            )
        )
        self._sesion.flush()
        return huella
