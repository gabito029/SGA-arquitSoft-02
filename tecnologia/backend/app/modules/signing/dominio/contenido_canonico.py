"""Contenido canónico que se firma en cada nivel y su huella SHA-256 (research §3; ADR-004).

Los campos son **fijos por nivel**, para que un cambio legítimo posterior (el despacho, el acta)
no invalide una firma anterior:

- ``VB_UNIDAD``, ``CONFORMIDAD_GU`` y ``APROBACION_ALMACEN``: ``id``, ``codigo``, ``unidad_id`` y
  ``categoria`` de la solicitud; los ítems (``item_id`` + ``cantidad_solicitada``) ordenados por
  ``item_id``; y el nivel, la decisión, el firmante (id, rol, órgano) y la fecha y hora.
- ``ACTA_RECEPCION``: lo anterior y, por ítem, ``cantidad_despachada``, ``cantidad_recibida`` y
  ``observacion``.
- **Nunca** se firman ``estado`` ni ``version``.

Python puro: la representación canónica es JSON ordenado y compacto en UTF-8.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.json_canonico import a_json_canonico
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma


@dataclass(frozen=True)
class LineaFirmable:
    item_id: uuid.UUID
    cantidad_solicitada: int
    cantidad_despachada: int | None = None
    cantidad_recibida: int | None = None
    observacion: str | None = None


@dataclass(frozen=True)
class DocumentoFirmable:
    """Los datos de la solicitud que entran en la firma, tal como están en la base de datos."""

    id: uuid.UUID
    codigo: str
    unidad_id: uuid.UUID
    categoria: str
    items: tuple[LineaFirmable, ...]


@dataclass(frozen=True)
class Firmante:
    id: uuid.UUID
    rol: str
    organo_id: uuid.UUID


def contenido_de_nivel(
    documento: DocumentoFirmable,
    nivel: NivelFirma,
    decision: DecisionFirma,
    firmante: Firmante,
    firmado_en: datetime,
) -> dict[str, Any]:
    """Arma el contenido firmado de ``nivel`` con los campos fijos de research §3."""
    es_acta = nivel is NivelFirma.ACTA_RECEPCION
    items: list[dict[str, Any]] = []
    for linea in sorted(documento.items, key=lambda li: str(li.item_id)):
        item: dict[str, Any] = {
            "item_id": linea.item_id,
            "cantidad_solicitada": linea.cantidad_solicitada,
        }
        if es_acta:
            item["cantidad_despachada"] = linea.cantidad_despachada
            item["cantidad_recibida"] = linea.cantidad_recibida
            item["observacion"] = linea.observacion
        items.append(item)
    return {
        "requerimiento": {
            "id": documento.id,
            "codigo": documento.codigo,
            "unidad_id": documento.unidad_id,
            "categoria": documento.categoria,
            "items": items,
        },
        "nivel": nivel,
        "decision": decision,
        "firmante": {"id": firmante.id, "rol": firmante.rol, "organo_id": firmante.organo_id},
        "firmado_en": firmado_en,
    }


def serializar(contenido: dict[str, Any]) -> bytes:
    """Bytes canónicos: los mismos datos dan los mismos bytes, sin importar el orden."""
    return a_json_canonico(contenido)


def huella_sha256(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()
