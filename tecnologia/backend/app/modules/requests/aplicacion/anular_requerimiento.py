"""Caso de uso: anular un requerimiento con justificación (T087; FR-022).

Solo el OFICIAL_LOGISTICA de la unidad (el router exige el rol; otra unidad responde 404), solo
desde BORRADOR (cualquier otro estado responde 409 TRANSICION_NO_PERMITIDA) y con motivo
obligatorio (422). La solicitud no se borra: queda ANULADA con el motivo en el historial.
"""

import uuid

from app.core.errores import DetalleError
from app.modules.requests.aplicacion.firmar_requerimiento import (
    bloquear_sin_cambios,
    cargar_visible,
)
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.aplicacion.registrar_requerimiento import entrada_historial, evento
from app.modules.requests.dominio.errores import MotivoObligatorio
from app.modules.requests.dominio.estado import AccionHistorial
from app.modules.requests.dominio.puertos import RegistroAuditoria, RepositorioRequerimientos
from app.modules.requests.dominio.requerimiento import Requerimiento


class AnularRequerimiento:
    def __init__(
        self, repositorio: RepositorioRequerimientos, auditoria: RegistroAuditoria
    ) -> None:
        self._repositorio = repositorio
        self._auditoria = auditoria

    def ejecutar(self, actor: Actor, requerimiento_id: uuid.UUID, motivo: str) -> Requerimiento:
        previo = cargar_visible(self._repositorio, actor, requerimiento_id)
        req = bloquear_sin_cambios(self._repositorio, previo)
        anterior = req.estado
        if not motivo or not motivo.strip():
            raise MotivoObligatorio(
                "Debe indicar el motivo de la anulación.",
                detalles=[DetalleError("motivo", "Indique el motivo de la anulación.")],
            )
        req.anular(motivo)
        limpio = motivo.strip()
        self._repositorio.guardar(req)
        self._repositorio.agregar_historial(
            entrada_historial(req, actor, AccionHistorial.ANULAR, anterior, motivo=limpio)
        )
        self._auditoria.registrar(evento(req, actor, "REQUERIMIENTO.ANULAR", motivo=limpio))
        return req
