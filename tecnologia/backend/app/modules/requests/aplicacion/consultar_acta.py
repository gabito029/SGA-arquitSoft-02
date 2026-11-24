"""Casos de uso de lectura: el acta de recepción y la verificación de integridad (T078;
FR-023 a FR-025). Usan la misma política de acceso que el detalle (lo ajeno responde 404); el
AUDITOR, que ve todo lo enviado, puede consultar y verificar.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.core.errores import NoEncontrado
from app.modules.requests.aplicacion.consultar_firmas import VistaFirma, VistasFirma
from app.modules.requests.aplicacion.consultar_requerimientos import ConstructorVistas, VistaItem
from app.modules.requests.aplicacion.firmar_requerimiento import cargar_visible, documento_firmable
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.puertos import (
    ConsultaCatalogo,
    ConsultaUsuarios,
    FirmasRequerimiento,
    RepositorioRequerimientos,
    VerificadorFirmas,
)
from app.modules.signing.dominio.tipos import NivelFirma, ResultadoVerificacion


@dataclass(frozen=True)
class VistaActa:
    id: uuid.UUID
    requerimiento_id: uuid.UUID
    firma: VistaFirma
    tiene_diferencias: bool
    items: list[VistaItem]


@dataclass(frozen=True)
class VistaVerificacionFirma:
    firma_id: uuid.UUID
    nivel: NivelFirma
    resultado: ResultadoVerificacion
    firmante: str
    firmado_en: datetime


@dataclass(frozen=True)
class VistaVerificacion:
    requerimiento_id: uuid.UUID
    resultado: ResultadoVerificacion
    firmas: list[VistaVerificacionFirma]


class ConsultarActa:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        firmas: FirmasRequerimiento,
        usuarios: ConsultaUsuarios,
        catalogo: ConsultaCatalogo,
    ) -> None:
        self._repositorio = repositorio
        self._firmas = firmas
        self._vistas_firma = VistasFirma(usuarios, catalogo)
        self._vistas = ConstructorVistas(catalogo)

    def ejecutar(self, actor: Actor, requerimiento_id: uuid.UUID) -> VistaActa:
        req = cargar_visible(self._repositorio, actor, requerimiento_id)
        acta = self._firmas.acta(req.id)
        firma = next(
            (f for f in self._firmas.firmas(req.id) if acta and f.id == acta.firma_id), None
        )
        if acta is None or firma is None:
            raise NoEncontrado("La solicitud todavía no tiene acta de recepción.")
        return VistaActa(
            id=acta.id,
            requerimiento_id=req.id,
            firma=self._vistas_firma.construir([firma])[0],
            tiene_diferencias=acta.tiene_diferencias,
            items=self._vistas.una(actor, req).items,
        )


class VerificarIntegridad:
    def __init__(
        self,
        repositorio: RepositorioRequerimientos,
        verificador: VerificadorFirmas,
        usuarios: ConsultaUsuarios,
    ) -> None:
        self._repositorio = repositorio
        self._verificador = verificador
        self._usuarios = usuarios

    def ejecutar(self, actor: Actor, requerimiento_id: uuid.UUID) -> VistaVerificacion:
        req = cargar_visible(self._repositorio, actor, requerimiento_id)
        verificacion = self._verificador.ejecutar(documento_firmable(req))
        nombres = self._usuarios.nombres([v.firma.firmante_id for v in verificacion.firmas])
        return VistaVerificacion(
            requerimiento_id=req.id,
            resultado=verificacion.resultado,
            firmas=[
                VistaVerificacionFirma(
                    firma_id=v.firma.id,
                    nivel=v.firma.nivel,
                    resultado=v.resultado,
                    firmante=nombres.get(v.firma.firmante_id, ""),
                    firmado_en=v.firma.firmado_en,
                )
                for v in verificacion.firmas
            ],
        )
