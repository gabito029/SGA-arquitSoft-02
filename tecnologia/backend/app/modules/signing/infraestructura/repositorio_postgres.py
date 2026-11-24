"""Adaptador del repositorio de firmas sobre PostgreSQL. Trabaja en la sesión de quien lo llama."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.identity.dominio.rol import Rol
from app.modules.signing.dominio.errores import NivelYaRegistrado
from app.modules.signing.dominio.puertos import ActaRegistrada, FirmaRegistrada
from app.modules.signing.dominio.tipos import NivelFirma
from app.modules.signing.infraestructura.modelos import ActaRecepcionModelo, FirmaModelo


def _registro(m: FirmaModelo) -> FirmaRegistrada:
    return FirmaRegistrada(
        id=m.id,
        requerimiento_id=m.requerimiento_id,
        nivel=m.nivel,
        decision=m.decision,
        firmante_id=m.firmante_id,
        rol=m.rol.value,
        organo_id=m.organo_id,
        contenido_canonico=m.contenido_canonico,
        huella_sha256=m.huella_sha256,
        firma=m.firma,
        metodo=m.metodo,
        clave_id=m.clave_id,
        firmado_en=m.firmado_en,
    )


class RepositorioFirmasPostgres:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def guardar(self, firma: FirmaRegistrada) -> None:
        modelo = FirmaModelo(
            id=firma.id,
            requerimiento_id=firma.requerimiento_id,
            nivel=firma.nivel,
            decision=firma.decision,
            firmante_id=firma.firmante_id,
            rol=Rol(firma.rol),
            organo_id=firma.organo_id,
            contenido_canonico=firma.contenido_canonico,
            huella_sha256=firma.huella_sha256,
            firma=firma.firma,
            metodo=firma.metodo,
            clave_id=firma.clave_id,
            firmado_en=firma.firmado_en,
        )
        try:
            # Punto de guardado: la violación de la restricción única no aborta la transacción.
            with self._sesion.begin_nested():
                self._sesion.add(modelo)
                self._sesion.flush()
        except IntegrityError as error:
            raise NivelYaRegistrado() from error

    def listar(self, requerimiento_id: uuid.UUID) -> list[FirmaRegistrada]:
        return [
            _registro(m)
            for m in self._sesion.scalars(
                select(FirmaModelo)
                .where(FirmaModelo.requerimiento_id == requerimiento_id)
                .order_by(FirmaModelo.firmado_en, FirmaModelo.id)
            )
        ]

    def guardar_acta(self, acta: ActaRegistrada) -> None:
        try:
            with self._sesion.begin_nested():
                self._sesion.add(
                    ActaRecepcionModelo(
                        id=acta.id,
                        requerimiento_id=acta.requerimiento_id,
                        firma_id=acta.firma_id,
                        tiene_diferencias=acta.tiene_diferencias,
                    )
                )
                self._sesion.flush()
        except IntegrityError as error:
            raise NivelYaRegistrado("El acta de recepción ya fue firmada.") from error

    def acta(self, requerimiento_id: uuid.UUID) -> ActaRegistrada | None:
        m = self._sesion.scalar(
            select(ActaRecepcionModelo).where(
                ActaRecepcionModelo.requerimiento_id == requerimiento_id
            )
        )
        if m is None:
            return None
        return ActaRegistrada(
            id=m.id,
            requerimiento_id=m.requerimiento_id,
            firma_id=m.firma_id,
            tiene_diferencias=m.tiene_diferencias,
            creado_en=m.creado_en,
        )

    def niveles(self, requerimiento_id: uuid.UUID) -> set[NivelFirma]:
        return set(
            self._sesion.scalars(
                select(FirmaModelo.nivel).where(FirmaModelo.requerimiento_id == requerimiento_id)
            )
        )
