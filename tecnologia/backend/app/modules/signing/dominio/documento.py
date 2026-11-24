"""Documentos oficiales firmados y su código de verificación (incremento 002; research §2 y §3;
data-model.md de 002). Python puro: sin ReportLab, sin disco y sin base de datos.

- ``DocumentoPdf``: lo que muestra el documento (encabezado, líneas y sellos). Es la fuente única
  de la vista en la página y del PDF.
- ``huella_contenido()``: SHA-256 del contenido canónico del documento; es la huella que se
  imprime en el PDF (la de los bytes no puede ir dentro del propio archivo).
- ``generar_codigo()``/``extraer_codigo()``: código ``SGA-XXXX-XXXX-XXXX`` aleatorio, impreso en
  cada página y en los metadatos del PDF.
"""

import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.core.json_canonico import a_json_canonico
from app.modules.signing.dominio.contenido_canonico import huella_sha256
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma


class TipoDocumento(StrEnum):
    REQUERIMIENTO = "REQUERIMIENTO"
    ACTA = "ACTA"


# Niveles cuyos sellos van en cada documento (clarificación 3 de la spec de 002).
NIVELES_DEL_DOCUMENTO: dict[TipoDocumento, tuple[NivelFirma, ...]] = {
    TipoDocumento.REQUERIMIENTO: (
        NivelFirma.VB_UNIDAD,
        NivelFirma.CONFORMIDAD_GU,
        NivelFirma.APROBACION_ALMACEN,
    ),
    TipoDocumento.ACTA: (NivelFirma.ACTA_RECEPCION,),
}

ETIQUETAS_NIVEL: dict[str, str] = {
    NivelFirma.VB_UNIDAD: "Visto bueno de la unidad",
    NivelFirma.CONFORMIDAD_GU: "Conformidad de la División/Brigada",
    NivelFirma.APROBACION_ALMACEN: "Aprobación del almacén",
    NivelFirma.ACTA_RECEPCION: "Acta de recepción",
}

ETIQUETAS_ROL: dict[str, str] = {
    "OFICIAL_LOGISTICA": "Oficial de logística",
    "COMANDANTE_UNIDAD": "Comandante de la unidad",
    "JEFE_LOGISTICA_GU": "Jefe de logística de la División/Brigada",
    "JEFE_ALMACEN": "Jefe de almacén",
    "ALMACENERO": "Almacenero",
    "AUDITOR": "Auditor",
}

ETIQUETAS_DECISION: dict[str, str] = {
    DecisionFirma.APROBAR: "Aprobó",
    DecisionFirma.RECHAZAR: "Rechazó",
}


@dataclass(frozen=True)
class Referencia:
    """Un órgano o un almacén tal como se imprime: código y nombre."""

    codigo: str
    nombre: str


@dataclass(frozen=True)
class SelloDocumento:
    """Una firma registrada (001) presentada como sello digital (FR-003)."""

    firma_id: uuid.UUID
    nivel: NivelFirma
    decision: DecisionFirma
    firmante: str
    rol: str
    organo: Referencia
    firmado_en: datetime
    metodo: str
    huella_sha256: str
    motivo: str | None = None


@dataclass(frozen=True)
class LineaDocumento:
    codigo: str
    descripcion: str
    unidad_medida: str
    categoria: str
    cantidad_solicitada: int
    cantidad_despachada: int | None = None
    cantidad_recibida: int | None = None
    observacion: str | None = None


@dataclass(frozen=True)
class DocumentoPdf:
    """El documento oficial de un requerimiento o de su acta de recepción."""

    tipo: TipoDocumento
    requerimiento_id: uuid.UUID
    numero: str
    unidad: Referencia
    gran_unidad: Referencia | None
    almacen: Referencia | None
    fecha: datetime | None
    lineas: tuple[LineaDocumento, ...]
    sellos: tuple[SelloDocumento, ...]
    tiene_diferencias: bool | None = None

    @property
    def firmas_incluidas(self) -> tuple[uuid.UUID, ...]:
        return tuple(s.firma_id for s in self.sellos)

    @property
    def ultima_firma_id(self) -> uuid.UUID | None:
        """La firma más reciente que incluye; None si todavía no hay sellos."""
        if not self.sellos:
            return None
        return max(self.sellos, key=lambda s: s.firmado_en).firma_id

    def contenido_canonico(self) -> bytes:
        def ref(r: Referencia | None) -> dict[str, str] | None:
            return None if r is None else {"codigo": r.codigo, "nombre": r.nombre}

        datos: dict[str, Any] = {
            "tipo": self.tipo,
            "requerimiento_id": self.requerimiento_id,
            "numero": self.numero,
            "unidad": ref(self.unidad),
            "gran_unidad": ref(self.gran_unidad),
            "almacen": ref(self.almacen),
            "fecha": self.fecha,
            "tiene_diferencias": self.tiene_diferencias,
            "lineas": [
                {
                    "codigo": li.codigo,
                    "cantidad_solicitada": li.cantidad_solicitada,
                    "cantidad_despachada": li.cantidad_despachada,
                    "cantidad_recibida": li.cantidad_recibida,
                    "observacion": li.observacion,
                }
                for li in self.lineas
            ],
            "sellos": [
                {"firma_id": s.firma_id, "huella_sha256": s.huella_sha256} for s in self.sellos
            ],
        }
        return a_json_canonico(datos)

    def huella_contenido(self) -> str:
        return huella_sha256(self.contenido_canonico())


@dataclass(frozen=True)
class DocumentoEmitido:
    """Un PDF emitido por el SGA (tabla ``documento_emitido``). Nunca se modifica."""

    id: uuid.UUID
    codigo_verificacion: str
    tipo: TipoDocumento
    requerimiento_id: uuid.UUID
    ultima_firma_id: uuid.UUID
    firmas_incluidas: tuple[uuid.UUID, ...]
    huella_contenido: str
    huella_sha256: str
    firma: str
    metodo: str
    clave_id: str
    clave_almacen: str
    tamano_bytes: int
    emitido_por: uuid.UUID
    organo_id: uuid.UUID
    emitido_en: datetime


# --- Código de verificación (research §3) ---

# Base32 sin caracteres ambiguos (sin I, O, 0 ni 1): 32 símbolos × 12 = 60 bits aleatorios.
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_PATRON_CODIGO = re.compile(rb"SGA-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}")


def generar_codigo() -> str:
    simbolos = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(12))
    return f"SGA-{simbolos[:4]}-{simbolos[4:8]}-{simbolos[8:]}"


def es_codigo_valido(codigo: str) -> bool:
    return _PATRON_CODIGO.fullmatch(codigo.encode("ascii", errors="replace")) is not None


def extraer_codigo(contenido: bytes) -> str | None:
    """El primer código de verificación que aparece en los bytes del PDF, o None."""
    encontrado = _PATRON_CODIGO.search(contenido)
    return encontrado.group(0).decode("ascii") if encontrado else None


def clave_almacen(requerimiento_id: uuid.UUID, tipo: TipoDocumento, codigo: str) -> str:
    """Dónde se guarda el PDF dentro del almacenamiento (research §7)."""
    return f"{requerimiento_id}/{tipo.value.lower()}-{codigo}.pdf"
