"""Verificación de integridad de todas las firmas de un requerimiento (T077; FR-024, FR-025,
EQ-02).

Para cada firma reconstruye el contenido canónico con los datos **actuales** de la base de datos
(los del requerimiento y los de la propia fila de firma: firmante, rol, órgano y fecha), con los
mismos campos que usó ``firmar_nivel`` para ese nivel (research §3: sin ``estado`` ni ``version``;
lo despachado, lo recibido y las observaciones solo en ACTA_RECEPCION). Luego recalcula la huella
y verifica la firma según su ``metodo``. Si cualquiera falla, el resultado global es ALTERADA.
"""

from app.modules.signing.aplicacion.servicio_firma import ServicioFirma
from app.modules.signing.dominio.contenido_canonico import DocumentoFirmable
from app.modules.signing.dominio.puertos import VerificacionFirma, VerificacionRequerimiento
from app.modules.signing.dominio.tipos import ResultadoVerificacion


class VerificarRequerimiento:
    def __init__(self, servicio: ServicioFirma) -> None:
        self._servicio = servicio

    def ejecutar(self, documento_actual: DocumentoFirmable) -> VerificacionRequerimiento:
        firmas = [
            VerificacionFirma(firma=f, resultado=self._servicio.verificar(f, documento_actual))
            for f in self._servicio.firmas(documento_actual.id)
        ]
        alterada = any(v.resultado is ResultadoVerificacion.ALTERADA for v in firmas)
        return VerificacionRequerimiento(
            requerimiento_id=documento_actual.id,
            resultado=ResultadoVerificacion.ALTERADA if alterada else ResultadoVerificacion.INTEGRA,
            firmas=firmas,
        )
