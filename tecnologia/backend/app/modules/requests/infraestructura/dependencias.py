"""Composición del módulo de requerimientos: arma los casos de uso con sus adaptadores.

``requests`` usa a ``catalog``, ``rules`` y ``audit`` solo a través de sus servicios públicos y de
su composición, nunca de sus tablas (plan → Arquitectura aplicada).
"""

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import obtener_configuracion
from app.core.unidad_trabajo import UnidadTrabajo
from app.modules.audit.infraestructura.dependencias import construir_registro_auditoria
from app.modules.catalog.aplicacion.consultar_catalogo import ConsultarCatalogo
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.catalog.infraestructura.dependencias import construir_consulta_catalogo
from app.modules.identity.infraestructura.dependencias import construir_consulta_usuarios
from app.modules.inventory.infraestructura.dependencias import construir_servicio_despacho
from app.modules.requests.aplicacion.consultar_firmas import ConsultarFirmas
from app.modules.requests.aplicacion.consultar_requerimientos import ConsultarRequerimientos
from app.modules.requests.aplicacion.despachar_requerimiento import DespacharRequerimiento
from app.modules.requests.aplicacion.enviar_requerimiento import EnviarRequerimiento
from app.modules.requests.aplicacion.firmar_requerimiento import FirmarRequerimiento
from app.modules.requests.aplicacion.registrar_requerimiento import RegistrarRequerimiento
from app.modules.requests.dominio.puertos import AlmacenResumen, ItemCatalogo, OrganoCatalogo
from app.modules.requests.infraestructura.repositorio_postgres import (
    RepositorioRequerimientosPostgres,
)
from app.modules.rules.dominio.regla_aprobacion import ReglaCologePorCategoriaOMonto
from app.modules.signing.infraestructura.dependencias import construir_servicio_firma


class ConsultaCatalogoServicio:
    """Adaptador del puerto ``ConsultaCatalogo`` sobre el servicio público del catálogo."""

    def __init__(self, catalogo: ConsultarCatalogo) -> None:
        self._catalogo = catalogo

    def items(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, ItemCatalogo]:
        return {
            i.id: ItemCatalogo(
                id=i.id,
                codigo=i.codigo,
                nombre=i.nombre,
                categoria=i.categoria,
                unidad_medida=i.unidad_medida,
                valor_unitario=Decimal(i.valor_unitario),
                activo=i.activo,
            )
            for i in self._catalogo.items_por_id(ids).values()
        }

    def organo(self, organo_id: uuid.UUID) -> OrganoCatalogo | None:
        o = self._catalogo.organo(organo_id)
        if o is None:
            return None
        return OrganoCatalogo(
            id=o.id, codigo=o.codigo, nombre=o.nombre, tipo=o.tipo, padre_id=o.padre_id
        )

    def almacen_por_categoria(self, categoria: Categoria) -> uuid.UUID | None:
        a = self._catalogo.almacen_por_categoria(categoria)
        return a.id if a else None

    def almacen(self, almacen_id: uuid.UUID) -> AlmacenResumen | None:
        a = self._catalogo.almacen(almacen_id)
        if a is None:
            return None
        servicio = self._catalogo.organo(a.organo_id)
        return AlmacenResumen(id=a.id, codigo=servicio.codigo if servicio else "", nombre=a.nombre)


def _catalogo(sesion: Session) -> ConsultaCatalogoServicio:
    return ConsultaCatalogoServicio(construir_consulta_catalogo(sesion))


def construir_registrar(sesion: Session) -> RegistrarRequerimiento:
    return RegistrarRequerimiento(
        repositorio=RepositorioRequerimientosPostgres(sesion),
        catalogo=_catalogo(sesion),
        auditoria=construir_registro_auditoria(sesion),
    )


def construir_enviar(uow: UnidadTrabajo) -> EnviarRequerimiento:
    sesion = uow.sesion
    return EnviarRequerimiento(
        repositorio=RepositorioRequerimientosPostgres(sesion),
        catalogo=_catalogo(sesion),
        # El umbral se lee de la configuración (ADR-008).
        regla=ReglaCologePorCategoriaOMonto(obtener_configuracion().umbral_monto_alto),
        auditoria=construir_registro_auditoria(sesion),
        transaccion=uow,
    )


def construir_firmar(sesion: Session) -> FirmarRequerimiento:
    return FirmarRequerimiento(
        repositorio=RepositorioRequerimientosPostgres(sesion),
        firmas=construir_servicio_firma(sesion),
        auditoria=construir_registro_auditoria(sesion),
    )


def construir_despachar(sesion: Session) -> DespacharRequerimiento:
    return DespacharRequerimiento(
        repositorio=RepositorioRequerimientosPostgres(sesion),
        inventario=construir_servicio_despacho(sesion),
        auditoria=construir_registro_auditoria(sesion),
    )


def construir_consultar_firmas(sesion: Session) -> ConsultarFirmas:
    return ConsultarFirmas(
        repositorio=RepositorioRequerimientosPostgres(sesion),
        firmas=construir_servicio_firma(sesion),
        usuarios=construir_consulta_usuarios(sesion),
        catalogo=_catalogo(sesion),
    )


def construir_consultar(sesion: Session) -> ConsultarRequerimientos:
    return ConsultarRequerimientos(
        repositorio=RepositorioRequerimientosPostgres(sesion),
        catalogo=_catalogo(sesion),
    )
