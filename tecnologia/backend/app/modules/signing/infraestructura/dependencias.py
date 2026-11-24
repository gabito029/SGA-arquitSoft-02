"""Composición del módulo de firma: el servicio público con el firmador Ed25519 configurado."""

from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.config import obtener_configuracion
from app.modules.signing.aplicacion.servicio_firma import ServicioFirma
from app.modules.signing.infraestructura.firmador_ed25519 import FirmadorEd25519
from app.modules.signing.infraestructura.repositorio_postgres import RepositorioFirmasPostgres


@lru_cache
def obtener_firmador() -> FirmadorEd25519:
    """La clave del sistema se carga una vez por proceso desde la configuración (ADR-004)."""
    configuracion = obtener_configuracion()
    return FirmadorEd25519.desde_pem_base64(
        configuracion.firma_clave_privada, configuracion.firma_clave_id
    )


def construir_servicio_firma(sesion: Session) -> ServicioFirma:
    return ServicioFirma(RepositorioFirmasPostgres(sesion), obtener_firmador())
