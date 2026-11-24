"""Documento oficial de un requerimiento y de su acta (incremento 002; FR-001 a FR-004, FR-014).

``ArmadorDocumento`` arma el ``DocumentoPdf`` del módulo de firma con los datos del requerimiento,
el catálogo, las firmas registradas y el motivo de un rechazo (que la firma de 001 no guarda: sale
de la línea de tiempo). Es la fuente única de la vista en la página y del PDF.

``ConsultarDocumento`` aplica antes la visibilidad de 001 (lo ajeno responde 404).
"""

import uuid
from dataclasses import dataclass

from app.core.errores import NoEncontrado
from app.modules.requests.aplicacion.firmar_requerimiento import cargar_visible
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.estado import AccionHistorial
from app.modules.requests.dominio.puertos import (
    ConsultaCatalogo,
    ConsultaUsuarios,
    FirmasRequerimiento,
    RepositorioRequerimientos,
)
from app.modules.requests.dominio.requerimiento import Requerimiento
from app.modules.signing.dominio.documento import (
    NIVELES_DEL_DOCUMENTO,
    DocumentoPdf,
    LineaDocumento,
    Referencia,
    SelloDocumento,
    TipoDocumento,
)
from app.modules.signing.dominio.tipos import DecisionFirma

MENSAJE_SIN_ACTA = "La solicitud todavía no tiene acta de recepción."


@dataclass(frozen=True)
class VistaDocumento:
    documento: DocumentoPdf
    huella_contenido: str
    pdf_disponible: bool


class ArmadorDocumento:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        firmas: FirmasRequerimiento,
        usuarios: ConsultaUsuarios,
        catalogo: ConsultaCatalogo,
    ) -> None:
        self._repositorio = repositorio
        self._firmas = firmas
        self._usuarios = usuarios
        self._catalogo = catalogo

    def _organo(self, organo_id: uuid.UUID | None) -> Referencia | None:
        if organo_id is None:
            return None
        o = self._catalogo.organo(organo_id)
        return Referencia(o.codigo, o.nombre) if o else Referencia("", "")

    def _almacen(self, almacen_id: uuid.UUID | None) -> Referencia | None:
        if almacen_id is None:
            return None
        a = self._catalogo.almacen(almacen_id)
        return Referencia(a.codigo, a.nombre) if a else None

    def _motivo_rechazo(self, req: Requerimiento) -> str | None:
        rechazos = [
            h for h in self._repositorio.historial(req.id) if h.accion is AccionHistorial.RECHAZAR
        ]
        return rechazos[-1].motivo if rechazos else None

    def armar(self, req: Requerimiento, tipo: TipoDocumento) -> DocumentoPdf:
        niveles = NIVELES_DEL_DOCUMENTO[tipo]
        firmas = sorted(
            (f for f in self._firmas.firmas(req.id) if f.nivel in niveles),
            key=lambda f: f.firmado_en,
        )
        if tipo is TipoDocumento.ACTA and not firmas:
            raise NoEncontrado(MENSAJE_SIN_ACTA)
        nombres = self._usuarios.nombres([f.firmante_id for f in firmas])
        motivo = (
            self._motivo_rechazo(req)
            if any(f.decision is DecisionFirma.RECHAZAR for f in firmas)
            else None
        )
        sellos = tuple(
            SelloDocumento(
                firma_id=f.id,
                nivel=f.nivel,
                decision=f.decision,
                firmante=nombres.get(f.firmante_id, ""),
                rol=str(f.rol),
                organo=self._organo(f.organo_id) or Referencia("", ""),
                firmado_en=f.firmado_en,
                metodo=f.metodo,
                huella_sha256=f.huella_sha256,
                motivo=motivo if f.decision is DecisionFirma.RECHAZAR else None,
            )
            for f in firmas
        )
        items = self._catalogo.items([i.item_id for i in req.items])
        es_acta = tipo is TipoDocumento.ACTA
        lineas = tuple(
            LineaDocumento(
                codigo=items[i.item_id].codigo if i.item_id in items else "",
                descripcion=items[i.item_id].nombre if i.item_id in items else "",
                unidad_medida=items[i.item_id].unidad_medida if i.item_id in items else "",
                categoria=req.categoria.value,
                cantidad_solicitada=i.cantidad_solicitada,
                cantidad_despachada=i.cantidad_despachada if es_acta else None,
                cantidad_recibida=i.cantidad_recibida if es_acta else None,
                observacion=i.observacion if es_acta else None,
            )
            for i in sorted(
                req.items,
                key=lambda i: items[i.item_id].codigo if i.item_id in items else str(i.item_id),
            )
        )
        acta = self._firmas.acta(req.id) if es_acta else None
        return DocumentoPdf(
            tipo=tipo,
            requerimiento_id=req.id,
            numero=req.codigo,
            unidad=self._organo(req.unidad_id) or Referencia("", ""),
            gran_unidad=self._organo(req.gran_unidad_id),
            almacen=self._almacen(req.almacen_id),
            fecha=req.creado_en,
            lineas=lineas,
            sellos=sellos,
            tiene_diferencias=acta.tiene_diferencias if acta else None,
        )


class ConsultarDocumento:
    def __init__(self, repositorio: RepositorioRequerimientos, armador: ArmadorDocumento) -> None:
        self._repositorio = repositorio
        self._armador = armador

    def ejecutar(
        self,
        actor: Actor,
        requerimiento_id: uuid.UUID,
        tipo: TipoDocumento = TipoDocumento.REQUERIMIENTO,
    ) -> VistaDocumento:
        req = cargar_visible(self._repositorio, actor, requerimiento_id)
        documento = self._armador.armar(req, tipo)
        return VistaDocumento(
            documento=documento,
            huella_contenido=documento.huella_contenido(),
            pdf_disponible=bool(documento.sellos),
        )
