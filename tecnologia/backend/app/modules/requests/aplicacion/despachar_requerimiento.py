"""Caso de uso: despachar un requerimiento APROBADO y descontar el stock (T069; HU07, RF06;
FR-017 a FR-020).

Solo actúa el ALMACENERO del almacén del requerimiento (los demás roles reciben 403 en el router
y otro almacén recibe 404 por la política de acceso). En una sola transacción:

1. Bloquea el requerimiento; si cambió mientras esperaba el bloqueo, ESTADO_CAMBIADO (409).
2. La entidad valida que esté APROBADA, que cada cantidad esté entre 0 y lo solicitado y que al
   menos un ítem tenga una cantidad mayor que 0 (422), y pasa a EN_TRANSITO.
3. El servicio de inventario bloquea el stock, valida que alcance (STOCK_INSUFICIENTE, 409) y
   registra los movimientos. Si falla, la Unidad de Trabajo deshace todo: nada queda a medias.
4. Guarda el estado y lo despachado, y registra historial y auditoría.
"""

import uuid
from dataclasses import dataclass

from app.modules.inventory.dominio.puertos import LineaDespacho
from app.modules.requests.aplicacion.firmar_requerimiento import (
    bloquear_sin_cambios,
    cargar_visible,
)
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.aplicacion.registrar_requerimiento import entrada_historial, evento
from app.modules.requests.dominio.estado import AccionHistorial
from app.modules.requests.dominio.puertos import (
    DespachoInventario,
    RegistroAuditoria,
    RepositorioRequerimientos,
)
from app.modules.requests.dominio.requerimiento import Requerimiento


@dataclass(frozen=True)
class CantidadDespacho:
    item_id: uuid.UUID
    cantidad: int


class DespacharRequerimiento:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        inventario: DespachoInventario,
        auditoria: RegistroAuditoria,
    ) -> None:
        self._repositorio = repositorio
        self._inventario = inventario
        self._auditoria = auditoria

    def ejecutar(
        self, actor: Actor, requerimiento_id: uuid.UUID, cantidades: list[CantidadDespacho]
    ) -> Requerimiento:
        previo = cargar_visible(self._repositorio, actor, requerimiento_id)
        req = bloquear_sin_cambios(self._repositorio, previo)
        anterior = req.estado
        req.despachar({c.item_id: c.cantidad for c in cantidades})

        despachado = [
            LineaDespacho(item_id=i.item_id, cantidad=i.cantidad_despachada or 0) for i in req.items
        ]
        self._inventario.despachar(
            almacen_id=req.almacen_id,
            requerimiento_id=req.id,
            usuario_id=actor.id,
            lineas=despachado,
        )
        self._repositorio.guardar(req)
        self._repositorio.agregar_historial(
            entrada_historial(req, actor, AccionHistorial.DESPACHAR, anterior)
        )
        self._auditoria.registrar(
            evento(
                req,
                actor,
                "REQUERIMIENTO.DESPACHAR",
                items=[
                    {"item_id": str(li.item_id), "cantidad": li.cantidad}
                    for li in sorted(despachado, key=lambda li: str(li.item_id))
                ],
            )
        )
        return req
