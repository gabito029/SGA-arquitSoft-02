"""Composición del módulo de firma: el servicio público con el firmador Ed25519 configurado y,
desde 002, los adaptadores de documentos (disco y ReportLab)."""

from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.config import obtener_configuracion
from app.modules.signing.aplicacion.emitir_documento import EmitirDocumento
from app.modules.signing.aplicacion.servicio_firma import ServicioFirma
from app.modules.signing.aplicacion.verificar_pdf import VerificarPdf
from app.modules.signing.aplicacion.verificar_requerimiento import VerificarRequerimiento
from app.modules.signing.infraestructura.almacen_documentos_disco import AlmacenDocumentosDisco
from app.modules.signing.infraestructura.firmador_ed25519 import FirmadorEd25519
from app.modules.signing.infraestructura.generador_pdf_reportlab import GeneradorPdfReportLab
from app.modules.signing.infraestructura.repositorio_documentos_postgres import (
    RepositorioDocumentosPostgres,
)
from app.modules.signing.infraestructura.repositorio_postgres import RepositorioFirmasPostgres


@lru_cache
def obtener_firmador() -> FirmadorEd25519:
    """La clave del sistema se carga una vez por proceso desde la configuración (ADR-004)."""
    configuracion = obtener_configuracion()
    return FirmadorEd25519.desde_pem_base64(
        configuracion.firma_clave_privada, configuracion.firma_clave_id
    )


def construir_servicio_firma(sesion: Session) -> ServicioFirma:
    return ServicioFirma(RepositorioFirmasPostgres(sesion), obtener_firmador())


def construir_verificador(sesion: Session) -> VerificarRequerimiento:
    return VerificarRequerimiento(construir_servicio_firma(sesion))


def obtener_almacen_documentos() -> AlmacenDocumentosDisco:
    """El almacenamiento de documentos de ADR-010; hoy, el disco local (volumen de Docker)."""
    return AlmacenDocumentosDisco(obtener_configuracion().documentos_dir)


@lru_cache
def obtener_generador_pdf() -> GeneradorPdfReportLab:
    return GeneradorPdfReportLab()


def construir_emitir_documento(sesion: Session) -> EmitirDocumento:
    """Emisión de PDF firmados (002): repositorio, disco (ADR-010), ReportLab y Ed25519."""
    return EmitirDocumento(
        RepositorioDocumentosPostgres(sesion),
        obtener_almacen_documentos(),
        obtener_generador_pdf(),
        obtener_firmador(),
    )


def construir_verificar_pdf(sesion: Session) -> VerificarPdf:
    """Verificación de un PDF subido (002, US5; EQ-02): registro de emitidos y Ed25519."""
    return VerificarPdf(RepositorioDocumentosPostgres(sesion), obtener_firmador())
