"""Descargar el PDF del requerimiento o del acta (incremento 002; US3 y US4; FR-008 a FR-015).

Aplica la visibilidad de 001 (lo ajeno responde 404), arma el documento con ``ArmadorDocumento`` y
pide al módulo de firma que lo emita o devuelva el ya emitido (``EmitirDocumento``). Las
solicitudes firmadas antes de 002 obtienen su PDF en la primera descarga (FR-015).
"""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.modules.requests.aplicacion.consultar_documento import ArmadorDocumento
from app.modules.requests.aplicacion.firmar_requerimiento import cargar_visible
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.puertos import RepositorioRequerimientos
from app.modules.signing.dominio.documento import DocumentoEmitido, DocumentoPdf, TipoDocumento


class EmisorDocumentos(Protocol):
    def ejecutar(
        self, documento: DocumentoPdf, emisor_id: uuid.UUID, organo_id: uuid.UUID
    ) -> tuple[DocumentoEmitido, bytes]: ...


@dataclass(frozen=True)
class PdfDescargado:
    nombre_archivo: str
    codigo_verificacion: str
    contenido: bytes


class DescargarPdf:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        armador: ArmadorDocumento,
        emisor: EmisorDocumentos,
    ) -> None:
        self._repositorio = repositorio
        self._armador = armador
        self._emisor = emisor

    def ejecutar(
        self,
        actor: Actor,
        requerimiento_id: uuid.UUID,
        tipo: TipoDocumento = TipoDocumento.REQUERIMIENTO,
    ) -> PdfDescargado:
        req = cargar_visible(self._repositorio, actor, requerimiento_id)
        documento = self._armador.armar(req, tipo)
        emitido, contenido = self._emisor.ejecutar(documento, actor.id, actor.organo_id)
        sufijo = "-acta" if tipo is TipoDocumento.ACTA else ""
        return PdfDescargado(
            nombre_archivo=f"{req.codigo}{sufijo}.pdf",
            codigo_verificacion=emitido.codigo_verificacion,
            contenido=contenido,
        )
