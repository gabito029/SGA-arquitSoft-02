"""Caso de uso de lectura: firmas registradas de un requerimiento (contrato ``Firma``).

Aplica la misma política de acceso que el detalle: lo ajeno responde 404.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.requests.aplicacion.consultar_requerimientos import Resumen
from app.modules.requests.aplicacion.firmar_requerimiento import cargar_visible
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.puertos import (
    ConsultaCatalogo,
    ConsultaUsuarios,
    FirmasRequerimiento,
    RepositorioRequerimientos,
)
from app.modules.signing.dominio.puertos import FirmaRegistrada
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma


@dataclass(frozen=True)
class VistaFirma:
    id: uuid.UUID
    nivel: NivelFirma
    decision: DecisionFirma
    firmante: str
    rol: str
    organo: Resumen
    huella_sha256: str
    metodo: str
    firmado_en: datetime


class VistasFirma:
    """Completa las firmas con el nombre del firmante y el resumen de su órgano."""

    def __init__(self, usuarios: ConsultaUsuarios, catalogo: ConsultaCatalogo) -> None:
        self._usuarios = usuarios
        self._catalogo = catalogo

    def _organo(self, organo_id: uuid.UUID) -> Resumen:
        o = self._catalogo.organo(organo_id)
        return Resumen(o.id, o.codigo, o.nombre) if o else Resumen(organo_id, "", "")

    def construir(self, firmas: list[FirmaRegistrada]) -> list[VistaFirma]:
        nombres = self._usuarios.nombres([f.firmante_id for f in firmas])
        return [
            VistaFirma(
                id=f.id,
                nivel=f.nivel,
                decision=f.decision,
                firmante=nombres.get(f.firmante_id, ""),
                rol=f.rol,
                organo=self._organo(f.organo_id),
                huella_sha256=f.huella_sha256,
                metodo=f.metodo,
                firmado_en=f.firmado_en,
            )
            for f in firmas
        ]


class ConsultarFirmas:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        firmas: FirmasRequerimiento,
        usuarios: ConsultaUsuarios,
        catalogo: ConsultaCatalogo,
    ) -> None:
        self._repositorio = repositorio
        self._firmas = firmas
        self._vistas = VistasFirma(usuarios, catalogo)

    def ejecutar(self, actor: Actor, requerimiento_id: uuid.UUID) -> list[VistaFirma]:
        req = cargar_visible(self._repositorio, actor, requerimiento_id)
        return self._vistas.construir(self._firmas.firmas(req.id))
