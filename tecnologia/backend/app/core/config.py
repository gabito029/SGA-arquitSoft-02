"""Configuración de la API, leída de variables de entorno (constitución, principio X).

Los secretos nunca se versionan: llegan por el entorno o por el archivo ``.env`` (ignorado por Git).
"""

from decimal import Decimal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        # El .env vive en tecnologia/; se busca también en la carpeta actual.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(description="URL de SQLAlchemy de la base de datos principal")
    database_url_test: str | None = None

    jwt_secreto: str = Field(min_length=16)
    jwt_minutos: int = Field(default=60, gt=0)

    firma_clave_privada: str = ""
    firma_clave_id: str = ""

    umbral_monto_alto: Decimal = Field(default=Decimal("50000"), ge=0)
    catalogo_cache_activa: bool = True

    contrasena_demo: str | None = None

    # Almacenamiento de los PDF firmados (ADR-010). En Docker es el volumen "documentos".
    documentos_dir: str = "/datos/documentos"
    # Tamaño máximo de un PDF subido para verificarlo (FR-016).
    pdf_tamano_maximo: int = Field(default=5 * 1024 * 1024, gt=0)


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Devuelve la configuración (una sola instancia por proceso)."""
    return Configuracion()  # type: ignore[call-arg]
