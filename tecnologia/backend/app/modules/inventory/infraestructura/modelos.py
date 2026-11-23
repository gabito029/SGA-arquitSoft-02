"""Tablas stock y movimiento (data-model.md §3).

Invariante EQ-03: stock.cantidad = Σ ENTRADA − Σ SALIDA_DESPACHO por (almacén, ítem).
``movimiento`` es inmutable (disparador de la migración 0002).
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_datos import Base
from app.core.tipos_bd import enum_pg
from app.modules.inventory.dominio.tipos import TipoMovimiento


class StockModelo(Base):
    __tablename__ = "stock"
    __table_args__ = (CheckConstraint("cantidad >= 0", name="cantidad_no_negativa"),)

    almacen_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("almacen.id"), primary_key=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("item.id"), primary_key=True)
    cantidad: Mapped[int] = mapped_column(Integer)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MovimientoModelo(Base):
    __tablename__ = "movimiento"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="cantidad_positiva"),
        CheckConstraint(
            "tipo <> 'SALIDA_DESPACHO' OR requerimiento_id IS NOT NULL",
            name="despacho_con_requerimiento",
        ),
        # data-model.md §8: movimientos por stock (invariante EQ-03).
        Index("ix_movimiento_almacen_id_item_id", "almacen_id", "item_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    almacen_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("almacen.id"))
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("item.id"))
    tipo: Mapped[TipoMovimiento] = mapped_column(enum_pg(TipoMovimiento, "tipo_movimiento"))
    cantidad: Mapped[int] = mapped_column(Integer)
    requerimiento_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("requerimiento.id")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
