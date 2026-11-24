"""Tabla registro_auditoria, encadenada e inmutable (data-model.md §5, ADR-005)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CHAR, BigInteger, DateTime, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_datos import Base
from app.core.tipos_bd import enum_pg
from app.modules.identity.dominio.rol import Rol


class RegistroAuditoriaModelo(Base):
    __tablename__ = "registro_auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tipo_evento: Mapped[str] = mapped_column(Text)
    entidad: Mapped[str] = mapped_column(Text)
    entidad_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    # Copias al momento del evento: el registro no depende de que el usuario siga existiendo.
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    rol: Mapped[Rol | None] = mapped_column(enum_pg(Rol, "rol"))
    organo_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    datos: Mapped[dict[str, Any]] = mapped_column(JSONB)
    huella_anterior: Mapped[str] = mapped_column(CHAR(64))
    huella: Mapped[str] = mapped_column(CHAR(64))
    # Lo fija la aplicación (no el servidor), porque forma parte de la huella.
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
