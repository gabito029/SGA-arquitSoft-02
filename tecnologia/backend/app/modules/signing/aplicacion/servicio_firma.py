"""Servicio público de firma digital (T060; ADR-004, research §3).

``firmar_nivel`` construye el contenido canónico del nivel, calcula la huella SHA-256, lo firma y
guarda la firma **dentro de la Unidad de Trabajo de quien lo llama** (no confirma ni deshace).
``verificar`` recalcula la huella con los datos que se le pasan y comprueba la firma.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from app.modules.signing.dominio.contenido_canonico import (
    DocumentoFirmable,
    Firmante,
    contenido_de_nivel,
    huella_sha256,
    serializar,
)
from app.modules.signing.dominio.puertos import (
    ActaRegistrada,
    FirmadorDocumentos,
    FirmaRegistrada,
    RepositorioFirmas,
)
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma, ResultadoVerificacion


class ServicioFirma:
    def __init__(
        self,
        repositorio: RepositorioFirmas,
        firmador: FirmadorDocumentos,
        reloj: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repositorio = repositorio
        self._firmador = firmador
        self._reloj = reloj

    def firmar_nivel(
        self,
        documento: DocumentoFirmable,
        nivel: NivelFirma,
        decision: DecisionFirma,
        firmante: Firmante,
    ) -> FirmaRegistrada:
        firmado_en = self._reloj()
        contenido = serializar(contenido_de_nivel(documento, nivel, decision, firmante, firmado_en))
        firma = FirmaRegistrada(
            id=uuid.uuid4(),
            requerimiento_id=documento.id,
            nivel=nivel,
            decision=decision,
            firmante_id=firmante.id,
            rol=firmante.rol,
            organo_id=firmante.organo_id,
            contenido_canonico=contenido.decode("utf-8"),
            huella_sha256=huella_sha256(contenido),
            firma=self._firmador.firmar(contenido),
            metodo=self._firmador.metodo,
            clave_id=self._firmador.clave_id,
            firmado_en=firmado_en,
        )
        self._repositorio.guardar(firma)
        return firma

    def registrar_acta(self, firma: FirmaRegistrada, tiene_diferencias: bool) -> ActaRegistrada:
        """Crea el acta de recepción apuntando a su firma, que debe ser de nivel ACTA_RECEPCION."""
        if firma.nivel is not NivelFirma.ACTA_RECEPCION:
            raise ValueError("El acta debe apuntar a una firma de nivel ACTA_RECEPCION.")
        acta = ActaRegistrada(
            id=uuid.uuid4(),
            requerimiento_id=firma.requerimiento_id,
            firma_id=firma.id,
            tiene_diferencias=tiene_diferencias,
        )
        self._repositorio.guardar_acta(acta)
        return acta

    def acta(self, requerimiento_id: uuid.UUID) -> ActaRegistrada | None:
        return self._repositorio.acta(requerimiento_id)

    def firmas(self, requerimiento_id: uuid.UUID) -> list[FirmaRegistrada]:
        return self._repositorio.listar(requerimiento_id)

    def niveles_firmados(self, requerimiento_id: uuid.UUID) -> set[NivelFirma]:
        return self._repositorio.niveles(requerimiento_id)

    def verificar(
        self, firma: FirmaRegistrada, documento_actual: DocumentoFirmable
    ) -> ResultadoVerificacion:
        """Reconstruye el contenido con los datos **actuales** y comprueba huella y firma."""
        firmante = Firmante(id=firma.firmante_id, rol=firma.rol, organo_id=firma.organo_id)
        contenido = serializar(
            contenido_de_nivel(
                documento_actual, firma.nivel, firma.decision, firmante, firma.firmado_en
            )
        )
        integra = (
            firma.metodo == self._firmador.metodo
            and huella_sha256(contenido) == firma.huella_sha256
            and self._firmador.verificar(contenido, firma.firma, firma.clave_id)
        )
        return ResultadoVerificacion.INTEGRA if integra else ResultadoVerificacion.ALTERADA
