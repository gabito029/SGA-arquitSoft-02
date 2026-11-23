"""Tabla usuario (data-model.md §2)."""

import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_datos import Base
from app.core.tipos_bd import enum_pg
from app.modules.identity.dominio.rol import Rol


class UsuarioModelo(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        # data-model.md usuario.almacen_id: obligatorio para jefe de almacén y almacenero.
        CheckConstraint(
            "rol NOT IN ('JEFE_ALMACEN', 'ALMACENERO') OR almacen_id IS NOT NULL",
            name="almacen_para_roles_de_almacen",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    usuario: Mapped[str] = mapped_column(Text, unique=True)
    nombre_completo: Mapped[str] = mapped_column(Text)
    hash_contrasena: Mapped[str] = mapped_column(Text)
    rol: Mapped[Rol] = mapped_column(enum_pg(Rol, "rol"))
    organo_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organo.id"))
    almacen_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("almacen.id"))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
