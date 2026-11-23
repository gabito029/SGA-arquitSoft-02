"""Tablas firma y acta_recepcion (data-model.md §5). Ambas son inmutables (migración 0002)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CHAR,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_datos import Base
from app.core.tipos_bd import enum_pg
from app.modules.identity.dominio.rol import Rol
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma


class FirmaModelo(Base):
    __tablename__ = "firma"
    __table_args__ = (
        # Cada nivel firma una sola vez (RN02, FR-013).
        UniqueConstraint("requerimiento_id", "nivel"),
        CheckConstraint(
            "nivel <> 'ACTA_RECEPCION' OR decision = 'APROBAR'", name="acta_siempre_aprueba"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    requerimiento_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("requerimiento.id"))
    nivel: Mapped[NivelFirma] = mapped_column(enum_pg(NivelFirma, "nivel_firma"))
    decision: Mapped[DecisionFirma] = mapped_column(enum_pg(DecisionFirma, "decision_firma"))
    firmante_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    rol: Mapped[Rol] = mapped_column(enum_pg(Rol, "rol"))
    organo_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organo.id"))
    contenido_canonico: Mapped[str] = mapped_column(Text)
    huella_sha256: Mapped[str] = mapped_column(CHAR(64))
    firma: Mapped[str] = mapped_column(Text)
    metodo: Mapped[str] = mapped_column(Text)
    clave_id: Mapped[str] = mapped_column(Text)
    firmado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActaRecepcionModelo(Base):
    __tablename__ = "acta_recepcion"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    # Una sola acta por requerimiento.
    requerimiento_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("requerimiento.id"), unique=True
    )
    # Apunta a la firma de nivel ACTA_RECEPCION; el caso de uso del acta (T076) lo valida.
    firma_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("firma.id"), unique=True)
    tiene_diferencias: Mapped[bool] = mapped_column(Boolean)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
