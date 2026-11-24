"""Tablas requerimiento, item_requerimiento e historial_requerimiento (data-model.md §4).

``historial_requerimiento`` es inmutable, y ``requerimiento`` e ``item_requerimiento`` quedan
protegidos en los estados finales (disparadores de la migración 0002).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_datos import Base
from app.core.tipos_bd import enum_pg
from app.modules.catalog.dominio.tipos import Categoria
from app.modules.identity.dominio.rol import Rol
from app.modules.requests.dominio.estado import AccionHistorial, EstadoRequerimiento


class RequerimientoModelo(Base):
    __tablename__ = "requerimiento"
    __table_args__ = (
        CheckConstraint("monto_total IS NULL OR monto_total >= 0", name="monto_no_negativo"),
        # data-model.md §8: bandejas de la unidad, de la Gran Unidad y del almacén.
        Index("ix_requerimiento_bandeja_unidad", "unidad_id", "estado", text("creado_en DESC")),
        Index(
            "ix_requerimiento_bandeja_gran_unidad",
            "gran_unidad_id",
            "estado",
            text("creado_en DESC"),
        ),
        Index("ix_requerimiento_bandeja_almacen", "almacen_id", "estado", text("creado_en DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    codigo: Mapped[str] = mapped_column(Text, unique=True)
    unidad_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organo.id"))
    gran_unidad_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organo.id"))
    almacen_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("almacen.id"))
    categoria: Mapped[Categoria] = mapped_column(enum_pg(Categoria, "categoria"))
    estado: Mapped[EstadoRequerimiento] = mapped_column(
        enum_pg(EstadoRequerimiento, "estado_requerimiento")
    )
    monto_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    creado_por: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))


class ItemRequerimientoModelo(Base):
    __tablename__ = "item_requerimiento"
    __table_args__ = (
        CheckConstraint("cantidad_solicitada > 0", name="solicitada_positiva"),
        CheckConstraint(
            "cantidad_despachada IS NULL OR "
            "(cantidad_despachada >= 0 AND cantidad_despachada <= cantidad_solicitada)",
            name="despachada_en_rango",
        ),
        CheckConstraint(
            "cantidad_recibida IS NULL OR cantidad_recibida >= 0", name="recibida_no_negativa"
        ),
    )

    # PK compuesta: sin ítems repetidos en un requerimiento.
    requerimiento_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("requerimiento.id"), primary_key=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("item.id"), primary_key=True)
    cantidad_solicitada: Mapped[int] = mapped_column(Integer)
    cantidad_despachada: Mapped[int | None] = mapped_column(Integer)
    cantidad_recibida: Mapped[int | None] = mapped_column(Integer)
    observacion: Mapped[str | None] = mapped_column(Text)


class HistorialRequerimientoModelo(Base):
    __tablename__ = "historial_requerimiento"
    __table_args__ = (
        CheckConstraint(
            "accion NOT IN ('RECHAZAR', 'ANULAR', 'ENVIO_BLOQUEADO') "
            "OR (motivo IS NOT NULL AND btrim(motivo) <> '')",
            name="motivo_obligatorio",
        ),
        # data-model.md §8: línea de tiempo.
        Index("ix_historial_requerimiento_linea_tiempo", "requerimiento_id", "ocurrido_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requerimiento_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("requerimiento.id"))
    accion: Mapped[AccionHistorial] = mapped_column(enum_pg(AccionHistorial, "accion_historial"))
    estado_anterior: Mapped[EstadoRequerimiento | None] = mapped_column(
        enum_pg(EstadoRequerimiento, "estado_requerimiento")
    )
    estado_nuevo: Mapped[EstadoRequerimiento] = mapped_column(
        enum_pg(EstadoRequerimiento, "estado_requerimiento")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    rol: Mapped[Rol] = mapped_column(enum_pg(Rol, "rol"))
    organo_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organo.id"))
    motivo: Mapped[str | None] = mapped_column(Text)
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
