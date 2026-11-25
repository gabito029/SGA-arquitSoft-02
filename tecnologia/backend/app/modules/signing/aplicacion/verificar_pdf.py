"""Verificación de un PDF subido (incremento 002; research §5; FR-016 a FR-019; EQ-02).

AUTENTICO solo si: (2) el archivo tiene un código de verificación; (3) el código corresponde a un
documento emitido; (4) quien verifica puede ver ese requerimiento (lo decide ``autorizar``, que
lanza 404); (5) la huella SHA-256 de los bytes es la registrada y la firma Ed25519 de esa huella es
válida; y (6) las firmas del requerimiento incluidas en el documento siguen íntegras con los datos
actuales (lo decide ``firmas_integras``, con la verificación de 001). Si falla cualquiera, ALTERADO
con el motivo. El paso (1), validar el archivo, lo hace la presentación.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.modules.signing.dominio.contenido_canonico import huella_sha256
from app.modules.signing.dominio.documento import DocumentoEmitido, extraer_codigo
from app.modules.signing.dominio.puertos import FirmadorDocumentos, RepositorioDocumentos
from app.modules.signing.dominio.tipos import ResultadoPdf

MOTIVO_AUTENTICO = (
    "El documento fue emitido por el SGA, no tiene cambios y sus firmas siguen íntegras."
)
MOTIVO_SIN_CODIGO = (
    "No es un documento emitido por el SGA: no tiene un código de verificación reconocible."
)
MOTIVO_CODIGO_DESCONOCIDO = (
    "El código de verificación no corresponde a ningún documento emitido por el SGA."
)
MOTIVO_BYTES = (
    "El archivo no coincide con el documento emitido: fue modificado después de su emisión."
)
MOTIVO_FIRMAS = "Los datos firmados del requerimiento fueron alterados después de la firma."


@dataclass(frozen=True)
class ResultadoVerificacionPdf:
    resultado: ResultadoPdf
    motivo: str
    documento: DocumentoEmitido | None = None


def _alterado(motivo: str, documento: DocumentoEmitido | None = None) -> ResultadoVerificacionPdf:
    return ResultadoVerificacionPdf(ResultadoPdf.ALTERADO, motivo, documento)


class VerificarPdf:
    def __init__(self, repositorio: RepositorioDocumentos, firmador: FirmadorDocumentos) -> None:
        self._repositorio = repositorio
        self._firmador = firmador

    def ejecutar(
        self,
        contenido: bytes,
        autorizar: Callable[[DocumentoEmitido], None],
        firmas_integras: Callable[[DocumentoEmitido], bool],
    ) -> ResultadoVerificacionPdf:
        codigo = extraer_codigo(contenido)
        if codigo is None:
            return _alterado(MOTIVO_SIN_CODIGO)
        emitido = self._repositorio.por_codigo(codigo)
        if emitido is None:
            return _alterado(MOTIVO_CODIGO_DESCONOCIDO)
        autorizar(emitido)
        bytes_iguales = huella_sha256(contenido) == emitido.huella_sha256
        if not bytes_iguales or not self._firmador.verificar(
            contenido, emitido.firma, emitido.clave_id
        ):
            return _alterado(MOTIVO_BYTES, emitido)
        if not firmas_integras(emitido):
            return _alterado(MOTIVO_FIRMAS, emitido)
        return ResultadoVerificacionPdf(ResultadoPdf.AUTENTICO, MOTIVO_AUTENTICO, emitido)
