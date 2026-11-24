"""Caso de uso: enviar un requerimiento por el conducto regular (FR-009, FR-012; RN03).

1. Bloquea la fila del requerimiento (``SELECT … FOR UPDATE``) y valida la jurisdicción (404).
2. Calcula ``monto_total`` = Σ cantidad × valor unitario del catálogo.
3. Consulta ``ReglaAprobacion``. Si exige al COLOGE, que llega en el incremento 002, registra
   ``ENVIO_BLOQUEADO`` con su motivo, **confirma** la transacción para que el intento quede en el
   historial y lanza ``RequiereCologe`` (409); el estado no cambia.
4. Si no, la entidad pasa a PENDIENTE_VB_UNIDAD y se registran el historial y la auditoría.
"""

import uuid
from decimal import Decimal

from app.modules.requests.aplicacion.politica_acceso import Actor, exigir_visible
from app.modules.requests.aplicacion.registrar_requerimiento import entrada_historial, evento
from app.modules.requests.dominio.errores import RequiereCologe
from app.modules.requests.dominio.estado import AccionHistorial
from app.modules.requests.dominio.puertos import (
    ConsultaCatalogo,
    RegistroAuditoria,
    RepositorioRequerimientos,
    Transaccion,
)
from app.modules.requests.dominio.requerimiento import Requerimiento
from app.modules.rules.dominio.regla_aprobacion import ReglaAprobacion


class EnviarRequerimiento:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        catalogo: ConsultaCatalogo,
        regla: ReglaAprobacion,
        auditoria: RegistroAuditoria,
        transaccion: Transaccion,
    ) -> None:
        self._repositorio = repositorio
        self._catalogo = catalogo
        self._regla = regla
        self._auditoria = auditoria
        self._transaccion = transaccion

    def _monto_total(self, req: Requerimiento) -> Decimal:
        valores = self._catalogo.items([i.item_id for i in req.items])
        total = sum(
            (valores[i.item_id].valor_unitario * i.cantidad_solicitada for i in req.items),
            Decimal("0"),
        )
        return total.quantize(Decimal("0.01"))

    def ejecutar(self, actor: Actor, requerimiento_id: uuid.UUID) -> Requerimiento:
        req = exigir_visible(actor, self._repositorio.obtener_para_actualizar(requerimiento_id))
        anterior = req.estado
        monto = self._monto_total(req)
        requiere_cologe = self._regla.requiere_cologe(req.categoria, monto)
        try:
            req.enviar(monto_total=monto, requiere_cologe=requiere_cologe)
        except RequiereCologe as bloqueo:
            self._repositorio.agregar_historial(
                entrada_historial(
                    req, actor, AccionHistorial.ENVIO_BLOQUEADO, anterior, motivo=bloqueo.mensaje
                )
            )
            self._auditoria.registrar(
                evento(
                    req,
                    actor,
                    "REQUERIMIENTO.ENVIO_BLOQUEADO",
                    monto_total=str(monto),
                    motivo=bloqueo.mensaje,
                )
            )
            # El intento bloqueado debe quedar aunque la petición responda 409 (FR-012).
            self._transaccion.confirmar()
            raise
        self._repositorio.guardar(req)
        self._repositorio.agregar_historial(
            entrada_historial(req, actor, AccionHistorial.ENVIAR, anterior)
        )
        self._auditoria.registrar(
            evento(req, actor, "REQUERIMIENTO.ENVIAR", monto_total=str(monto))
        )
        return req
