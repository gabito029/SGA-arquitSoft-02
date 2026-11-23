"""Representación canónica en JSON: claves ordenadas, sin espacios y en UTF-8 (research §3).

La misma estructura produce siempre los mismos bytes, sin importar el orden en que se armó.
La usan la auditoría encadenada (huella de cada registro) y la firma digital.
"""

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


def _convertir(valor: Any) -> Any:
    if isinstance(valor, uuid.UUID):
        return str(valor)
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            raise ValueError("Las fechas canónicas deben tener zona horaria")
        return valor.astimezone(UTC).isoformat(timespec="microseconds")
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, Enum):
        return valor.value
    raise TypeError(f"Tipo no admitido en el JSON canónico: {type(valor).__name__}")


def a_json_canonico(datos: Any) -> bytes:
    return json.dumps(
        datos,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_convertir,
    ).encode("utf-8")
