"""Caso de uso de lectura: la línea de tiempo de un requerimiento (T083; RF08, FR-026 a FR-028).

Cada entrada dice qué pasó, quién (nombre y rol), en qué órgano, cuándo y desde qué estado. Usa la
misma política de acceso que el detalle (lo ajeno responde 404). Es de solo lectura: no existe
ningún caso de uso ni endpoint para editar o borrar el historial (EQ-08).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.requests.aplicacion.consultar_requerimientos import Resumen
from app.modules.requests.aplicacion.firmar_requerimiento import cargar_visible
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.estado import AccionHistorial, EstadoRequerimiento
from app.modules.requests.dominio.puertos import (
    ConsultaCatalogo,
    ConsultaUsuarios,
    RepositorioRequerimientos,
)


@dataclass(frozen=True)
class VistaHistorial:
    accion: AccionHistorial
    estado_anterior: EstadoRequerimiento | None
    estado_nuevo: EstadoRequerimiento
    usuario: str
    rol: str
    organo: Resumen
    motivo: str | None
    ocurrido_en: datetime


class ConsultarHistorial:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        usuarios: ConsultaUsuarios,
        catalogo: ConsultaCatalogo,
    ) -> None:
        self._repositorio = repositorio
        self._usuarios = usuarios
        self._catalogo = catalogo

    def _organo(self, organo_id: uuid.UUID) -> Resumen:
        o = self._catalogo.organo(organo_id)
        return Resumen(o.id, o.codigo, o.nombre) if o else Resumen(organo_id, "", "")

    def ejecutar(self, actor: Actor, requerimiento_id: uuid.UUID) -> list[VistaHistorial]:
        req = cargar_visible(self._repositorio, actor, requerimiento_id)
        entradas = self._repositorio.historial(req.id)
        nombres = self._usuarios.nombres([e.usuario_id for e in entradas])
        return [
            VistaHistorial(
                accion=e.accion,
                estado_anterior=e.estado_anterior,
                estado_nuevo=e.estado_nuevo,
                usuario=nombres.get(e.usuario_id, ""),
                rol=e.rol,
                organo=self._organo(e.organo_id),
                motivo=e.motivo,
                ocurrido_en=e.ocurrido_en,
            )
            for e in entradas
        ]
