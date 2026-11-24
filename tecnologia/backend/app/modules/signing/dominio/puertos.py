"""Puertos del módulo de firma (inversión de dependencias; el firmador real y el doble de prueba
cumplen el mismo contrato, principio de Liskov). Python puro."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma


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
