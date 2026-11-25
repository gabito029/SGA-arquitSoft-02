"""Verificar un PDF subido por el usuario (incremento 002; US5; FR-016 a FR-019; EQ-02).

Paso 1 (aquí): el archivo no está vacío, empieza con ``%PDF-`` y pesa como máximo el límite de la
configuración; si no, 422 sin verificar nada. Los pasos 2 a 6 los hace ``VerificarPdf`` del módulo
de firma; este caso de uso le da la visibilidad de 001 (paso 4: lo ajeno responde 404) y la
verificación de las firmas incluidas con los datos actuales de la base de datos (paso 6).
"""

from dataclasses import dataclass, replace
from typing import Protocol

from app.core.errores import DetalleError, Validacion
from app.modules.requests.aplicacion.consultar_documento import ArmadorDocumento
from app.modules.requests.aplicacion.firmar_requerimiento import cargar_visible, documento_firmable
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.puertos import RepositorioRequerimientos, VerificadorFirmas
from app.modules.signing.dominio.documento import DocumentoEmitido, DocumentoPdf
from app.modules.signing.dominio.tipos import ResultadoVerificacion


class VerificadorPdf(Protocol):
    def ejecutar(self, contenido: bytes, autorizar, firmas_integras): ...


@dataclass(frozen=True)
class VistaVerificacionPdf:
    resultado: str
    motivo: str
    emitido: DocumentoEmitido | None
    requerimiento_codigo: str | None
    documento: DocumentoPdf | None


def _invalido(mensaje: str) -> Validacion:
    return Validacion(mensaje, detalles=[DetalleError("archivo", mensaje)])


class VerificarPdfSubido:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        verificador_pdf: VerificadorPdf,
        verificador_firmas: VerificadorFirmas,
        armador: ArmadorDocumento,
        tamano_maximo: int,
    ) -> None:
        self._repositorio = repositorio
        self._verificador_pdf = verificador_pdf
        self._verificador_firmas = verificador_firmas
        self._armador = armador
        self._tamano_maximo = tamano_maximo

    def validar(self, contenido: bytes) -> None:
        if not contenido:
            raise _invalido("El archivo está vacío.")
        if len(contenido) > self._tamano_maximo:
            megas = self._tamano_maximo // (1024 * 1024)
            raise _invalido(f"El archivo supera el tamaño máximo de {megas} MB.")
        if not contenido.startswith(b"%PDF-"):
            raise _invalido("El archivo no es un PDF.")

    def ejecutar(self, actor: Actor, contenido: bytes) -> VistaVerificacionPdf:
        self.validar(contenido)
        visibles: dict = {}

        def autorizar(emitido: DocumentoEmitido) -> None:
            visibles["req"] = cargar_visible(self._repositorio, actor, emitido.requerimiento_id)

        def firmas_integras(emitido: DocumentoEmitido) -> bool:
            verificacion = self._verificador_firmas.ejecutar(documento_firmable(visibles["req"]))
            resultados = {v.firma.id: v.resultado for v in verificacion.firmas}
            return all(
                resultados.get(firma_id) is ResultadoVerificacion.INTEGRA
                for firma_id in emitido.firmas_incluidas
            )

        resultado = self._verificador_pdf.ejecutar(contenido, autorizar, firmas_integras)
        req = visibles.get("req")
        documento = None
        if req is not None and resultado.documento is not None:
            # Los sellos que contiene el documento emitido, para mostrarlos al verificar (FR-019).
            actual = self._armador.armar(req, resultado.documento.tipo)
            incluidas = set(resultado.documento.firmas_incluidas)
            documento = replace(
                actual, sellos=tuple(s for s in actual.sellos if s.firma_id in incluidas)
            )
        return VistaVerificacionPdf(
            resultado=resultado.resultado.value,
            motivo=resultado.motivo,
            emitido=resultado.documento,
            requerimiento_codigo=req.codigo if req is not None else None,
            documento=documento,
        )
