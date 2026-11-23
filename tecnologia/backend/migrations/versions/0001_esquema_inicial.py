"""Esquema inicial del incremento 001: tablas, enums, restricciones e índices (data-model.md).

Revision ID: 0001
Revises:
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Enums de PostgreSQL (data-model.md). Se crean una vez y se comparten entre tablas.
ENUMS: dict[str, tuple[str, ...]] = {
    "tipo_organo": ("UNIDAD", "GRAN_UNIDAD", "COLOGE", "SERVICIO"),
    "categoria": ("INTENDENCIA", "MATERIAL_GUERRA"),
    "rol": (
        "OFICIAL_LOGISTICA",
        "COMANDANTE_UNIDAD",
        "JEFE_LOGISTICA_GU",
        "JEFE_ALMACEN",
        "ALMACENERO",
        "AUDITOR",
    ),
    "tipo_movimiento": ("ENTRADA", "SALIDA_DESPACHO"),
    "estado_requerimiento": (
        "BORRADOR",
        "PENDIENTE_VB_UNIDAD",
        "PENDIENTE_CONFORMIDAD",
        "PENDIENTE_AUTORIZACION_COLOGE",
        "PENDIENTE_APROBACION",
        "APROBADA",
        "RECHAZADA",
        "ANULADA",
        "EN_TRANSITO",
        "CONFIRMADA",
    ),
    "accion_historial": (
        "CREAR",
        "ENVIAR",
        "ENVIO_BLOQUEADO",
        "FIRMAR",
        "RECHAZAR",
        "ANULAR",
        "DESPACHAR",
        "FIRMAR_ACTA",
    ),
    "nivel_firma": ("VB_UNIDAD", "CONFORMIDAD_GU", "APROBACION_ALMACEN", "ACTA_RECEPCION"),
    "decision_firma": ("APROBAR", "RECHAZAR"),
}


def _enum(nombre: str) -> postgresql.ENUM:
    return postgresql.ENUM(*ENUMS[nombre], name=nombre, create_type=False)


def _uuid_pk() -> sa.Column:
    return sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False)


def _momento(nombre: str) -> sa.Column:
    return sa.Column(
        nombre, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    enlace = op.get_bind()
    for nombre in ENUMS:
        _enum(nombre).create(enlace, checkfirst=False)

    # --- Catálogo (data-model.md §1) ---
    op.create_table(
        "organo",
        _uuid_pk(),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("tipo", _enum("tipo_organo"), nullable=False),
        sa.Column("padre_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "tipo <> 'UNIDAD' OR padre_id IS NOT NULL", name=op.f("ck_organo_unidad_con_padre")
        ),
        sa.ForeignKeyConstraint(
            ["padre_id"], ["organo.id"], name=op.f("fk_organo_padre_id_organo")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organo")),
        sa.UniqueConstraint("codigo", name=op.f("uq_organo_codigo")),
    )
    op.create_table(
        "almacen",
        _uuid_pk(),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("organo_id", sa.Uuid(), nullable=False),
        sa.Column("categoria", _enum("categoria"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organo_id"], ["organo.id"], name=op.f("fk_almacen_organo_id_organo")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_almacen")),
    )
    op.create_table(
        "item",
        _uuid_pk(),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("categoria", _enum("categoria"), nullable=False),
        sa.Column("unidad_medida", sa.Text(), nullable=False),
        sa.Column("valor_unitario", sa.Numeric(12, 2), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("valor_unitario >= 0", name=op.f("ck_item_valor_unitario_no_negativo")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_item")),
        sa.UniqueConstraint("codigo", name=op.f("uq_item_codigo")),
    )
    op.create_index(
        "ix_item_categoria_activos",
        "item",
        ["categoria"],
        postgresql_where=sa.text("activo"),
    )

    # --- Identidad (data-model.md §2) ---
    op.create_table(
        "usuario",
        _uuid_pk(),
        sa.Column("usuario", sa.Text(), nullable=False),
        sa.Column("nombre_completo", sa.Text(), nullable=False),
        sa.Column("hash_contrasena", sa.Text(), nullable=False),
        sa.Column("rol", _enum("rol"), nullable=False),
        sa.Column("organo_id", sa.Uuid(), nullable=False),
        sa.Column("almacen_id", sa.Uuid(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint(
            "rol NOT IN ('JEFE_ALMACEN', 'ALMACENERO') OR almacen_id IS NOT NULL",
            name=op.f("ck_usuario_almacen_para_roles_de_almacen"),
        ),
        sa.ForeignKeyConstraint(
            ["almacen_id"], ["almacen.id"], name=op.f("fk_usuario_almacen_id_almacen")
        ),
        sa.ForeignKeyConstraint(
            ["organo_id"], ["organo.id"], name=op.f("fk_usuario_organo_id_organo")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
        # data-model.md §8: inicio de sesión.
        sa.UniqueConstraint("usuario", name=op.f("uq_usuario_usuario")),
    )

    # --- Requerimientos (data-model.md §4) ---
    op.create_table(
        "requerimiento",
        _uuid_pk(),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("unidad_id", sa.Uuid(), nullable=False),
        sa.Column("gran_unidad_id", sa.Uuid(), nullable=False),
        sa.Column("almacen_id", sa.Uuid(), nullable=False),
        sa.Column("categoria", _enum("categoria"), nullable=False),
        sa.Column("estado", _enum("estado_requerimiento"), nullable=False),
        sa.Column("monto_total", sa.Numeric(14, 2), nullable=True),
        sa.Column("creado_por", sa.Uuid(), nullable=False),
        _momento("creado_en"),
        _momento("actualizado_en"),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "monto_total IS NULL OR monto_total >= 0",
            name=op.f("ck_requerimiento_monto_no_negativo"),
        ),
        sa.ForeignKeyConstraint(
            ["almacen_id"], ["almacen.id"], name=op.f("fk_requerimiento_almacen_id_almacen")
        ),
        sa.ForeignKeyConstraint(
            ["creado_por"], ["usuario.id"], name=op.f("fk_requerimiento_creado_por_usuario")
        ),
        sa.ForeignKeyConstraint(
            ["gran_unidad_id"],
            ["organo.id"],
            name=op.f("fk_requerimiento_gran_unidad_id_organo"),
        ),
        sa.ForeignKeyConstraint(
            ["unidad_id"], ["organo.id"], name=op.f("fk_requerimiento_unidad_id_organo")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_requerimiento")),
        sa.UniqueConstraint("codigo", name=op.f("uq_requerimiento_codigo")),
    )
    # data-model.md §8: bandejas por estado, recientes primero.
    op.create_index(
        "ix_requerimiento_bandeja_unidad",
        "requerimiento",
        ["unidad_id", "estado", sa.text("creado_en DESC")],
    )
    op.create_index(
        "ix_requerimiento_bandeja_gran_unidad",
        "requerimiento",
        ["gran_unidad_id", "estado", sa.text("creado_en DESC")],
    )
    op.create_index(
        "ix_requerimiento_bandeja_almacen",
        "requerimiento",
        ["almacen_id", "estado", sa.text("creado_en DESC")],
    )

    op.create_table(
        "item_requerimiento",
        sa.Column("requerimiento_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("cantidad_solicitada", sa.Integer(), nullable=False),
        sa.Column("cantidad_despachada", sa.Integer(), nullable=True),
        sa.Column("cantidad_recibida", sa.Integer(), nullable=True),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "cantidad_solicitada > 0", name=op.f("ck_item_requerimiento_solicitada_positiva")
        ),
        sa.CheckConstraint(
            "cantidad_despachada IS NULL OR "
            "(cantidad_despachada >= 0 AND cantidad_despachada <= cantidad_solicitada)",
            name=op.f("ck_item_requerimiento_despachada_en_rango"),
        ),
        sa.CheckConstraint(
            "cantidad_recibida IS NULL OR cantidad_recibida >= 0",
            name=op.f("ck_item_requerimiento_recibida_no_negativa"),
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["item.id"], name=op.f("fk_item_requerimiento_item_id_item")
        ),
        sa.ForeignKeyConstraint(
            ["requerimiento_id"],
            ["requerimiento.id"],
            name=op.f("fk_item_requerimiento_requerimiento_id_requerimiento"),
        ),
        sa.PrimaryKeyConstraint("requerimiento_id", "item_id", name=op.f("pk_item_requerimiento")),
    )

    op.create_table(
        "historial_requerimiento",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("requerimiento_id", sa.Uuid(), nullable=False),
        sa.Column("accion", _enum("accion_historial"), nullable=False),
        sa.Column("estado_anterior", _enum("estado_requerimiento"), nullable=True),
        sa.Column("estado_nuevo", _enum("estado_requerimiento"), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("rol", _enum("rol"), nullable=False),
        sa.Column("organo_id", sa.Uuid(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        _momento("ocurrido_en"),
        sa.CheckConstraint(
            "accion NOT IN ('RECHAZAR', 'ANULAR', 'ENVIO_BLOQUEADO') "
            "OR (motivo IS NOT NULL AND btrim(motivo) <> '')",
            name=op.f("ck_historial_requerimiento_motivo_obligatorio"),
        ),
        sa.ForeignKeyConstraint(
            ["organo_id"], ["organo.id"], name=op.f("fk_historial_requerimiento_organo_id_organo")
        ),
        sa.ForeignKeyConstraint(
            ["requerimiento_id"],
            ["requerimiento.id"],
            name=op.f("fk_historial_requerimiento_requerimiento_id_requerimiento"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_historial_requerimiento_usuario_id_usuario"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_historial_requerimiento")),
    )
    # data-model.md §8: línea de tiempo.
    op.create_index(
        "ix_historial_requerimiento_linea_tiempo",
        "historial_requerimiento",
        ["requerimiento_id", "ocurrido_en"],
    )

    # --- Inventario (data-model.md §3) ---
    op.create_table(
        "stock",
        sa.Column("almacen_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        _momento("actualizado_en"),
        sa.CheckConstraint("cantidad >= 0", name=op.f("ck_stock_cantidad_no_negativa")),
        sa.ForeignKeyConstraint(
            ["almacen_id"], ["almacen.id"], name=op.f("fk_stock_almacen_id_almacen")
        ),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], name=op.f("fk_stock_item_id_item")),
        sa.PrimaryKeyConstraint("almacen_id", "item_id", name=op.f("pk_stock")),
    )
    op.create_table(
        "movimiento",
        _uuid_pk(),
        sa.Column("almacen_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", _enum("tipo_movimiento"), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("requerimiento_id", sa.Uuid(), nullable=True),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        _momento("ocurrido_en"),
        sa.CheckConstraint("cantidad > 0", name=op.f("ck_movimiento_cantidad_positiva")),
        sa.CheckConstraint(
            "tipo <> 'SALIDA_DESPACHO' OR requerimiento_id IS NOT NULL",
            name=op.f("ck_movimiento_despacho_con_requerimiento"),
        ),
        sa.ForeignKeyConstraint(
            ["almacen_id"], ["almacen.id"], name=op.f("fk_movimiento_almacen_id_almacen")
        ),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], name=op.f("fk_movimiento_item_id_item")),
        sa.ForeignKeyConstraint(
            ["requerimiento_id"],
            ["requerimiento.id"],
            name=op.f("fk_movimiento_requerimiento_id_requerimiento"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name=op.f("fk_movimiento_usuario_id_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movimiento")),
    )
    # data-model.md §8: movimientos por stock (invariante EQ-03).
    op.create_index("ix_movimiento_almacen_id_item_id", "movimiento", ["almacen_id", "item_id"])

    # --- Firma digital (data-model.md §5) ---
    op.create_table(
        "firma",
        _uuid_pk(),
        sa.Column("requerimiento_id", sa.Uuid(), nullable=False),
        sa.Column("nivel", _enum("nivel_firma"), nullable=False),
        sa.Column("decision", _enum("decision_firma"), nullable=False),
        sa.Column("firmante_id", sa.Uuid(), nullable=False),
        sa.Column("rol", _enum("rol"), nullable=False),
        sa.Column("organo_id", sa.Uuid(), nullable=False),
        sa.Column("contenido_canonico", sa.Text(), nullable=False),
        sa.Column("huella_sha256", sa.CHAR(64), nullable=False),
        sa.Column("firma", sa.Text(), nullable=False),
        sa.Column("metodo", sa.Text(), nullable=False),
        sa.Column("clave_id", sa.Text(), nullable=False),
        _momento("firmado_en"),
        sa.CheckConstraint(
            "nivel <> 'ACTA_RECEPCION' OR decision = 'APROBAR'",
            name=op.f("ck_firma_acta_siempre_aprueba"),
        ),
        sa.ForeignKeyConstraint(
            ["firmante_id"], ["usuario.id"], name=op.f("fk_firma_firmante_id_usuario")
        ),
        sa.ForeignKeyConstraint(
            ["organo_id"], ["organo.id"], name=op.f("fk_firma_organo_id_organo")
        ),
        sa.ForeignKeyConstraint(
            ["requerimiento_id"],
            ["requerimiento.id"],
            name=op.f("fk_firma_requerimiento_id_requerimiento"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_firma")),
        # RN02, FR-013: cada nivel firma una sola vez (también índice de las firmas, §8).
        sa.UniqueConstraint(
            "requerimiento_id", "nivel", name=op.f("uq_firma_requerimiento_id_nivel")
        ),
    )
    op.create_table(
        "acta_recepcion",
        _uuid_pk(),
        sa.Column("requerimiento_id", sa.Uuid(), nullable=False),
        sa.Column("firma_id", sa.Uuid(), nullable=False),
        sa.Column("tiene_diferencias", sa.Boolean(), nullable=False),
        _momento("creado_en"),
        sa.ForeignKeyConstraint(
            ["firma_id"], ["firma.id"], name=op.f("fk_acta_recepcion_firma_id_firma")
        ),
        sa.ForeignKeyConstraint(
            ["requerimiento_id"],
            ["requerimiento.id"],
            name=op.f("fk_acta_recepcion_requerimiento_id_requerimiento"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_acta_recepcion")),
        sa.UniqueConstraint("firma_id", name=op.f("uq_acta_recepcion_firma_id")),
        sa.UniqueConstraint("requerimiento_id", name=op.f("uq_acta_recepcion_requerimiento_id")),
    )

    # --- Auditoría encadenada (data-model.md §5, ADR-005) ---
    op.create_table(
        "registro_auditoria",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tipo_evento", sa.Text(), nullable=False),
        sa.Column("entidad", sa.Text(), nullable=False),
        sa.Column("entidad_id", sa.Uuid(), nullable=True),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("rol", _enum("rol"), nullable=True),
        sa.Column("organo_id", sa.Uuid(), nullable=True),
        sa.Column("datos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("huella_anterior", sa.CHAR(64), nullable=False),
        sa.Column("huella", sa.CHAR(64), nullable=False),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_registro_auditoria")),
    )


def downgrade() -> None:
    for tabla in (
        "registro_auditoria",
        "acta_recepcion",
        "firma",
        "movimiento",
        "stock",
        "historial_requerimiento",
        "item_requerimiento",
        "requerimiento",
        "usuario",
        "item",
        "almacen",
        "organo",
    ):
        op.drop_table(tabla)
    enlace = op.get_bind()
    for nombre in reversed(list(ENUMS)):
        _enum(nombre).drop(enlace, checkfirst=False)
