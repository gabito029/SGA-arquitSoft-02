"""Puertos del módulo de firma (inversión de dependencias; el firmador real y el doble de prueba
cumplen el mismo contrato, principio de Liskov). Python puro."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.modules.signing.dominio.documento import DocumentoEmitido, DocumentoPdf, TipoDocumento
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma, ResultadoVerificacion


@dataclass(frozen=True)
class FirmaRegistrada:
    """Una firma guardada (data-model.md firma)."""

    id: uuid.UUID
    requerimiento_id: uuid.UUID
    nivel: NivelFirma
    decision: DecisionFirma
    firmante_id: uuid.UUID
    rol: str
    organo_id: uuid.UUID
    contenido_canonico: str
    huella_sha256: str
    firma: str
    metodo: str
    clave_id: str
    firmado_en: datetime


@dataclass(frozen=True)
class ActaRegistrada:
    """El acta de recepción (data-model.md acta_recepcion), con la firma ACTA_RECEPCION."""

    id: uuid.UUID
    requerimiento_id: uuid.UUID
    firma_id: uuid.UUID
    tiene_diferencias: bool
    creado_en: datetime | None = None


@dataclass(frozen=True)
class VerificacionFirma:
    firma: FirmaRegistrada
    resultado: ResultadoVerificacion


@dataclass(frozen=True)
class VerificacionRequerimiento:
    requerimiento_id: uuid.UUID
    resultado: ResultadoVerificacion
    firmas: list[VerificacionFirma]


class FirmadorDocumentos(Protocol):
    metodo: str
    clave_id: str

    def firmar(self, contenido: bytes) -> str:
        """Firma ``contenido`` y devuelve la firma en base64."""
        ...

    def verificar(self, contenido: bytes, firma: str, clave_id: str) -> bool:
        """True si ``firma`` corresponde a ``contenido`` con la clave ``clave_id``."""
        ...


class RepositorioFirmas(Protocol):
    def guardar(self, firma: FirmaRegistrada) -> None:
        """Inserta la firma; si el nivel ya firmó, lanza ``NivelYaRegistrado``."""
        ...

    def listar(self, requerimiento_id: uuid.UUID) -> list[FirmaRegistrada]: ...

    def niveles(self, requerimiento_id: uuid.UUID) -> set[NivelFirma]: ...

    def guardar_acta(self, acta: ActaRegistrada) -> None:
        """Inserta el acta; si el requerimiento ya tiene una, lanza ``NivelYaRegistrado``."""
        ...

    def acta(self, requerimiento_id: uuid.UUID) -> ActaRegistrada | None: ...


# --- Documentos PDF (incremento 002; ADR-010) ---


class AlmacenDocumentos(Protocol):
    """Dónde se guardan los PDF firmados. Cambiar el disco por otro almacenamiento es otro
    adaptador de este puerto; los casos de uso no cambian (ADR-010, abierto/cerrado)."""

    def guardar(self, clave: str, contenido: bytes) -> None:
        """Guarda ``contenido``; si ``clave`` ya existe lanza ``DocumentoExistente`` (nunca
        sobrescribe). No hay método para borrar."""
        ...

    def leer(self, clave: str) -> bytes:
        """Devuelve los bytes guardados; si no existen lanza ``DocumentoNoEncontrado``."""
        ...


class GeneradorPdf(Protocol):
    def generar(self, documento: DocumentoPdf, codigo: str, huella_contenido: str) -> bytes:
        """Los bytes del PDF del documento, con el código en cada página y en los metadatos."""
        ...


class RepositorioDocumentos(Protocol):
    def buscar(
        self, requerimiento_id: uuid.UUID, tipo: TipoDocumento, ultima_firma_id: uuid.UUID
    ) -> DocumentoEmitido | None: ...

    def por_codigo(self, codigo: str) -> DocumentoEmitido | None: ...

    def guardar(self, documento: DocumentoEmitido) -> None:
        """Inserta la fila; si el estado firmado ya tiene documento lanza ``DocumentoExistente``."""
        ...
