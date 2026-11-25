"""Emisión de un PDF firmado (incremento 002; research §1 y §4; FR-009 a FR-013).

Un PDF por estado firmado del documento (requerimiento o acta): si ya se emitió para su última
firma, se lee del almacenamiento y se comprueba su huella antes de entregarlo (FR-013). Si no, se
genera, se calcula la huella SHA-256 de **sus bytes**, se firma con la clave del sistema (ADR-004),
se guarda el archivo sin sobrescribir (ADR-010) y se registra la fila, dentro de la Unidad de
Trabajo de quien lo llama.

Si dos peticiones emiten a la vez, el índice único rechaza la segunda fila y esta devuelve el
documento ya emitido; su archivo queda huérfano, sin nombre referenciado y sin servirse.

Sin ReportLab, sin disco y sin base de datos: solo puertos.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from app.core.errores import Conflicto
from app.modules.signing.dominio.contenido_canonico import huella_sha256
from app.modules.signing.dominio.documento import (
    DocumentoEmitido,
    DocumentoPdf,
    clave_almacen,
    generar_codigo,
)
from app.modules.signing.dominio.errores import DocumentoExistente, DocumentoInconsistente
from app.modules.signing.dominio.puertos import (
    AlmacenDocumentos,
    FirmadorDocumentos,
    GeneradorPdf,
    RepositorioDocumentos,
)


class SinFirmas(Conflicto):
    codigo_por_defecto = "SIN_FIRMAS"
    mensaje_por_defecto = "La solicitud todavía no tiene firmas: no hay un documento firmado."


class EmitirDocumento:
    def __init__(
        self,
        repositorio: RepositorioDocumentos,
        almacen: AlmacenDocumentos,
        generador: GeneradorPdf,
        firmador: FirmadorDocumentos,
        reloj: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repositorio = repositorio
        self._almacen = almacen
        self._generador = generador
        self._firmador = firmador
        self._reloj = reloj

    def leer_verificado(self, emitido: DocumentoEmitido) -> bytes:
        """Los bytes guardados, solo si coinciden con su huella y su firma (FR-013)."""
        contenido = self._almacen.leer(emitido.clave_almacen)
        if huella_sha256(contenido) != emitido.huella_sha256 or not self._firmador.verificar(
            contenido, emitido.firma, emitido.clave_id
        ):
            raise DocumentoInconsistente()
        return contenido

    def ejecutar(
        self, documento: DocumentoPdf, emisor_id: uuid.UUID, organo_id: uuid.UUID
    ) -> tuple[DocumentoEmitido, bytes]:
        ultima = documento.ultima_firma_id
        if ultima is None:
            raise SinFirmas()
        existente = self._repositorio.buscar(documento.requerimiento_id, documento.tipo, ultima)
        if existente is not None:
            return existente, self.leer_verificado(existente)

        codigo = generar_codigo()
        huella_contenido = documento.huella_contenido()
        pdf = self._generador.generar(documento, codigo, huella_contenido)
        emitido = DocumentoEmitido(
            id=uuid.uuid4(),
            codigo_verificacion=codigo,
            tipo=documento.tipo,
            requerimiento_id=documento.requerimiento_id,
            ultima_firma_id=ultima,
            firmas_incluidas=documento.firmas_incluidas,
            huella_contenido=huella_contenido,
            huella_sha256=huella_sha256(pdf),
            firma=self._firmador.firmar(pdf),
            metodo=self._firmador.metodo,
            clave_id=self._firmador.clave_id,
            clave_almacen=clave_almacen(documento.requerimiento_id, documento.tipo, codigo),
            tamano_bytes=len(pdf),
            emitido_por=emisor_id,
            organo_id=organo_id,
            emitido_en=self._reloj(),
        )
        self._almacen.guardar(emitido.clave_almacen, pdf)
        try:
            self._repositorio.guardar(emitido)
        except DocumentoExistente:
            # Otra petición emitió este mismo estado firmado al mismo tiempo.
            otro = self._repositorio.buscar(documento.requerimiento_id, documento.tipo, ultima)
            if otro is None:
                raise
            return otro, self.leer_verificado(otro)
        return emitido, pdf
