"""Tablas del catálogo: organo, almacen e item (data-model.md §1)."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_datos import Base
from app.core.tipos_bd import enum_pg
from app.modules.catalog.dominio.tipos import Categoria, TipoOrgano


class OrganoModelo(Base):
    __tablename__ = "organo"
    __table_args__ = (
        # data-model.md organo.padre_id: una UNIDAD DEBE tener padre (ADR-009).
        CheckConstraint("tipo <> 'UNIDAD' OR padre_id IS NOT NULL", name="unidad_con_padre"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    codigo: Mapped[str] = mapped_column(Text, unique=True)
    nombre: Mapped[str] = mapped_column(Text)
    tipo: Mapped[TipoOrgano] = mapped_column(enum_pg(TipoOrgano, "tipo_organo"))
    padre_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("organo.id"))


class AlmacenModelo(Base):
    __tablename__ = "almacen"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(Text)
    organo_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organo.id"))
    categoria: Mapped[Categoria] = mapped_column(enum_pg(Categoria, "categoria"))


class ItemModelo(Base):
    __tablename__ = "item"
    __table_args__ = (
        CheckConstraint("valor_unitario >= 0", name="valor_unitario_no_negativo"),
        # data-model.md §8: catálogo por categoría, solo ítems activos.
        Index("ix_item_categoria_activos", "categoria", postgresql_where=text("activo")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    codigo: Mapped[str] = mapped_column(Text, unique=True)
    nombre: Mapped[str] = mapped_column(Text)
    categoria: Mapped[Categoria] = mapped_column(enum_pg(Categoria, "categoria"))
    unidad_medida: Mapped[str] = mapped_column(Text)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
