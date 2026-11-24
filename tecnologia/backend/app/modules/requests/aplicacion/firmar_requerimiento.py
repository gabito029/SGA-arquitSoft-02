"""Caso de uso: firmar (aprobar) o rechazar en el nivel actual del conducto regular (T061;
HU03, HU05, RF03, RF05; FR-009 a FR-016).

Todo ocurre en una sola Unidad de Trabajo:

1. Lee la solicitud y comprueba la jurisdicción con la política de acceso (lo ajeno responde 404).
2. La bloquea (``SELECT … FOR UPDATE``). Si mientras esperaba el bloqueo otra transacción la
   cambió (``version`` distinta), responde 409 ESTADO_CAMBIADO: dos firmas concurrentes dejan una
   sola registrada.
3. El nivel sale del estado (PENDIENTE_VB_UNIDAD → VB_UNIDAD, PENDIENTE_CONFORMIDAD →
   CONFORMIDAD_GU, PENDIENTE_APROBACION → APROBACION_ALMACEN) y debe ser el del rol del firmante.
4. La entidad aplica la transición: un nivel no firma dos veces (NIVEL_YA_FIRMADO), un estado que
   no corresponde responde TRANSICION_NO_PERMITIDA y rechazar exige motivo.
5. Firma con Ed25519 (servicio de ``signing``), guarda el estado y registra historial y auditoría.
"""

import uuid
from dataclasses import dataclass

from app.core.errores import DetalleError
from app.modules.requests.aplicacion.politica_acceso import NIVEL_POR_ROL, Actor, exigir_visible
from app.modules.requests.aplicacion.registrar_requerimiento import entrada_historial, evento
from app.modules.requests.dominio.errores import (
    EstadoCambiado,
    MotivoObligatorio,
    TransicionNoPermitida,
)
from app.modules.requests.dominio.estado import AccionHistorial, EstadoRequerimiento
from app.modules.requests.dominio.puertos import FirmasRequerimiento, RegistroAuditoria
from app.modules.requests.dominio.puertos import RepositorioRequerimientos as Repositorio
from app.modules.requests.dominio.requerimiento import Requerimiento
from app.modules.signing.dominio.contenido_canonico import (
    DocumentoFirmable,
    Firmante,
    LineaFirmable,
)
from app.modules.signing.dominio.puertos import FirmaRegistrada
from app.modules.signing.dominio.tipos import DecisionFirma


def documento_firmable(req: Requerimiento) -> DocumentoFirmable:
    """Los datos de la solicitud que entran en la firma (research §3)."""
    return DocumentoFirmable(
        id=req.id,
        codigo=req.codigo,
        unidad_id=req.unidad_id,
        categoria=req.categoria.value,
        items=tuple(
            LineaFirmable(
                item_id=i.item_id,
                cantidad_solicitada=i.cantidad_solicitada,
                cantidad_despachada=i.cantidad_despachada,
                cantidad_recibida=i.cantidad_recibida,
                observacion=i.observacion,
            )
            for i in req.items
        ),
    )


def firmante_de(actor: Actor) -> Firmante:
    return Firmante(id=actor.id, rol=actor.rol.value, organo_id=actor.organo_id)


def cargar_visible(repositorio: Repositorio, actor: Actor, requerimiento_id: uuid.UUID):
    """Lee la solicitud sin bloquearla y comprueba que el usuario la vea (404 si no)."""
    req = repositorio.obtener(requerimiento_id)
    rechazado_desde = (
        repositorio.estado_previo_al_rechazo(req.id)
        if req is not None and req.estado is EstadoRequerimiento.RECHAZADA
        else None
    )
    return exigir_visible(actor, req, rechazado_desde)


def bloquear_sin_cambios(repositorio: Repositorio, previo: Requerimiento) -> Requerimiento:
    """Bloquea la fila; si cambió mientras se esperaba el bloqueo, responde ESTADO_CAMBIADO."""
    req = repositorio.obtener_para_actualizar(previo.id)
    if req is None or req.version != previo.version:
        raise EstadoCambiado()
    return req


@dataclass(frozen=True)
class ResultadoFirma:
    requerimiento: Requerimiento
    firma: FirmaRegistrada


class FirmarRequerimiento:
    def __init__(
        self,
        repositorio: Repositorio,
        firmas: FirmasRequerimiento,
        auditoria: RegistroAuditoria,
    ) -> None:
        self._repositorio = repositorio
        self._firmas = firmas
        self._auditoria = auditoria

    def ejecutar(
        self,
        actor: Actor,
        requerimiento_id: uuid.UUID,
        decision: DecisionFirma,
        motivo: str | None = None,
    ) -> ResultadoFirma:
        previo = cargar_visible(self._repositorio, actor, requerimiento_id)
        req = bloquear_sin_cambios(self._repositorio, previo)
        req.niveles_firmados = self._firmas.niveles_firmados(req.id)

        nivel = NIVEL_POR_ROL.get(actor.rol)
        if nivel is None:
            raise TransicionNoPermitida("Su rol no firma en el conducto regular.")
        anterior = req.estado
        if decision is DecisionFirma.RECHAZAR:
            if motivo is None or not motivo.strip():
                raise MotivoObligatorio(
                    "Debe indicar el motivo del rechazo.",
                    detalles=[DetalleError("motivo", "Indique el motivo del rechazo.")],
                )
            req.rechazar(nivel, motivo)
            accion, motivo_historial = AccionHistorial.RECHAZAR, motivo.strip()
        else:
            req.firmar(nivel)
            accion, motivo_historial = AccionHistorial.FIRMAR, None

        firma = self._firmas.firmar_nivel(
            documento_firmable(req), nivel, decision, firmante_de(actor)
        )
        self._repositorio.guardar(req)
        self._repositorio.agregar_historial(
            entrada_historial(req, actor, accion, anterior, motivo=motivo_historial)
        )
        self._auditoria.registrar(
            evento(
                req,
                actor,
                f"REQUERIMIENTO.{accion.value}",
                nivel=nivel.value,
                decision=decision.value,
                firma_id=str(firma.id),
                huella_sha256=firma.huella_sha256,
                **({"motivo": motivo_historial} if motivo_historial else {}),
            )
        )
        return ResultadoFirma(requerimiento=req, firma=firma)
