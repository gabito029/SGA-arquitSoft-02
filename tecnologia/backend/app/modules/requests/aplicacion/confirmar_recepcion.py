"""Caso de uso: firmar el acta de recepción (T076; HU08, RF07; FR-021, FR-023).

Solo actúa el OFICIAL_LOGISTICA de la unidad solicitante (el router exige el rol y la política de
acceso, la unidad), con el requerimiento EN_TRANSITO. Todo va en una sola transacción y **en este
orden**, porque el disparador de la migración 0002 bloquea los ítems cuando el requerimiento ya
está en un estado final:

1. La entidad registra lo recibido y las observaciones por ítem (y calcula las diferencias).
2. Se firma el nivel ACTA_RECEPCION con el contenido canónico del acta (research §3).
3. Se crea el acta, que apunta a esa firma.
4. Se guardan los ítems y **después** el estado CONFIRMADA; luego historial y auditoría.
"""

import uuid
from dataclasses import dataclass

from app.modules.requests.aplicacion.firmar_requerimiento import (
    bloquear_sin_cambios,
    cargar_visible,
    documento_firmable,
    firmante_de,
)
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.aplicacion.registrar_requerimiento import entrada_historial, evento
from app.modules.requests.dominio.estado import AccionHistorial
from app.modules.requests.dominio.puertos import (
    FirmasRequerimiento,
    RegistroAuditoria,
    RepositorioRequerimientos,
)
from app.modules.requests.dominio.requerimiento import Recepcion, Requerimiento
from app.modules.signing.dominio.puertos import ActaRegistrada, FirmaRegistrada
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma


@dataclass(frozen=True)
class LineaRecepcion:
    item_id: uuid.UUID
    cantidad_recibida: int
    observacion: str | None = None


@dataclass(frozen=True)
class ResultadoActa:
    requerimiento: Requerimiento
    firma: FirmaRegistrada
    acta: ActaRegistrada


class ConfirmarRecepcion:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        firmas: FirmasRequerimiento,
        auditoria: RegistroAuditoria,
    ) -> None:
        self._repositorio = repositorio
        self._firmas = firmas
        self._auditoria = auditoria

    def ejecutar(
        self, actor: Actor, requerimiento_id: uuid.UUID, recepcion: list[LineaRecepcion]
    ) -> ResultadoActa:
        previo = cargar_visible(self._repositorio, actor, requerimiento_id)
        req = bloquear_sin_cambios(self._repositorio, previo)
        req.niveles_firmados = self._firmas.niveles_firmados(req.id)
        anterior = req.estado

        # 1. Lo recibido (la entidad valida el estado, la cobertura y las cantidades).
        tiene_diferencias = req.firmar_acta(
            {
                li.item_id: Recepcion(
                    cantidad_recibida=li.cantidad_recibida, observacion=li.observacion
                )
                for li in recepcion
            }
        )
        # 2. La firma del acta y 3. el acta que apunta a ella.
        firma = self._firmas.firmar_nivel(
            documento_firmable(req),
            NivelFirma.ACTA_RECEPCION,
            DecisionFirma.APROBAR,
            firmante_de(actor),
        )
        acta = self._firmas.registrar_acta(firma, tiene_diferencias)
        # 4. Ítems antes que el estado final (lo hace el repositorio), historial y auditoría.
        self._repositorio.guardar(req)
        self._repositorio.agregar_historial(
            entrada_historial(req, actor, AccionHistorial.FIRMAR_ACTA, anterior)
        )
        self._auditoria.registrar(
            evento(
                req,
                actor,
                "REQUERIMIENTO.FIRMAR_ACTA",
                acta_id=str(acta.id),
                firma_id=str(firma.id),
                huella_sha256=firma.huella_sha256,
                tiene_diferencias=tiene_diferencias,
            )
        )
        return ResultadoActa(requerimiento=req, firma=firma, acta=acta)
