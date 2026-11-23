"""Esquemas de entrada y salida de requerimientos (contracts/openapi.yaml: RequerimientoEntrada,
Requerimiento, PaginaRequerimientos)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.catalog.dominio.tipos import Categoria
from app.modules.requests.aplicacion.consultar_requerimientos import (
    PaginaVistas,
    Resumen,
    VistaRequerimiento,
)
from app.modules.requests.aplicacion.politica_acceso import Accion
from app.modules.requests.aplicacion.registrar_requerimiento import LineaEntrada
from app.modules.requests.dominio.estado import EstadoRequerimiento

# --- Entrada ---


class LineaRequerimientoEntrada(BaseModel):
    item_id: uuid.UUID
    cantidad: int = Field(ge=1, description="Cantidad entera positiva")


class RequerimientoEntrada(BaseModel):
    items: list[LineaRequerimientoEntrada] = Field(min_length=1)

    @field_validator("items")
    @classmethod
    def _sin_repetidos(
        cls, items: list[LineaRequerimientoEntrada]
    ) -> list[LineaRequerimientoEntrada]:
        ids = [i.item_id for i in items]
        if len(set(ids)) != len(ids):
            raise ValueError("La solicitud no puede repetir un ítem.")
        return items

    def a_lineas(self) -> list[LineaEntrada]:
        return [LineaEntrada(item_id=i.item_id, cantidad=i.cantidad) for i in self.items]


# --- Salida ---


class OrganoResumenSalida(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str

    @classmethod
    def desde(cls, r: Resumen | None) -> "OrganoResumenSalida | None":
        return cls(id=r.id, codigo=r.codigo, nombre=r.nombre) if r else None


class ItemSalida(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    categoria: Categoria
    unidad_medida: str
    valor_unitario: str


class ItemRequerimientoSalida(BaseModel):
    item: ItemSalida
    cantidad_solicitada: int
    cantidad_despachada: int | None = None
    cantidad_recibida: int | None = None
    observacion: str | None = None


class RequerimientoSalida(BaseModel):
    id: uuid.UUID
    codigo: str
    estado: EstadoRequerimiento
    categoria: Categoria
    unidad: OrganoResumenSalida
    gran_unidad: OrganoResumenSalida | None = None
    almacen: OrganoResumenSalida | None = None
    monto_total: str | None = None
    items: list[ItemRequerimientoSalida]
    creado_en: datetime | None
    actualizado_en: datetime | None = None
    acciones_disponibles: list[Accion]

    @classmethod
    def desde_vista(cls, v: VistaRequerimiento) -> "RequerimientoSalida":
        return cls(
            id=v.id,
            codigo=v.codigo,
            estado=v.estado,
            categoria=v.categoria,
            unidad=OrganoResumenSalida(
                id=v.unidad.id, codigo=v.unidad.codigo, nombre=v.unidad.nombre
            ),
            gran_unidad=OrganoResumenSalida.desde(v.gran_unidad),
            almacen=OrganoResumenSalida.desde(v.almacen),
            monto_total=f"{v.monto_total:.2f}" if v.monto_total is not None else None,
            items=[
                ItemRequerimientoSalida(
                    item=ItemSalida(
                        id=i.item.id,
                        codigo=i.item.codigo,
                        nombre=i.item.nombre,
                        categoria=i.item.categoria,
                        unidad_medida=i.item.unidad_medida,
                        valor_unitario=f"{i.item.valor_unitario:.2f}",
                    ),
                    cantidad_solicitada=i.cantidad_solicitada,
                    cantidad_despachada=i.cantidad_despachada,
                    cantidad_recibida=i.cantidad_recibida,
                    observacion=i.observacion,
                )
                for i in v.items
            ],
            creado_en=v.creado_en,
            actualizado_en=v.actualizado_en,
            acciones_disponibles=v.acciones_disponibles,
        )


class PaginaRequerimientosSalida(BaseModel):
    items: list[RequerimientoSalida]
    total: int
    page: int
    size: int

    @classmethod
    def desde_pagina(cls, p: PaginaVistas) -> "PaginaRequerimientosSalida":
        return cls(
            items=[RequerimientoSalida.desde_vista(v) for v in p.items],
            total=p.total,
            page=p.page,
            size=p.size,
        )
