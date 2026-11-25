"""Tabla documento_emitido: los PDF firmados del incremento 002 (data-model.md de 002; ADR-004,
ADR-010).

- Una emisión por estado firmado: único (requerimiento_id, tipo, ultima_firma_id).
- El código de verificación es único.
- Inmutable: reutiliza ``rechazar_modificacion()`` de la migración 0002 (sin UPDATE ni DELETE).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documento_emitido",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("codigo_verificacion", sa.String(20), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("requerimiento_id", sa.Uuid(), nullable=False),
        sa.Column("ultima_firma_id", sa.Uuid(), nullable=False),
        sa.Column("firmas_incluidas", postgresql.JSONB(), nullable=False),
        sa.Column("huella_contenido", sa.CHAR(64), nullable=False),
        sa.Column("huella_sha256", sa.CHAR(64), nullable=False),
        sa.Column("firma", sa.Text(), nullable=False),
        sa.Column("metodo", sa.String(40), nullable=False),
        sa.Column("clave_id", sa.String(64), nullable=False),
        sa.Column("clave_almacen", sa.String(200), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("emitido_por", sa.Uuid(), nullable=False),
        sa.Column("organo_id", sa.Uuid(), nullable=False),
        sa.Column(
            "emitido_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "tipo IN ('REQUERIMIENTO', 'ACTA')", name=op.f("ck_documento_emitido_tipo_valido")
        ),
        sa.CheckConstraint("tamano_bytes > 0", name=op.f("ck_documento_emitido_tamano_positivo")),
        sa.ForeignKeyConstraint(
            ["requerimiento_id"],
            ["requerimiento.id"],
            name=op.f("fk_documento_emitido_requerimiento_id_requerimiento"),
        ),
        sa.ForeignKeyConstraint(
            ["ultima_firma_id"],
            ["firma.id"],
            name=op.f("fk_documento_emitido_ultima_firma_id_firma"),
        ),
        sa.ForeignKeyConstraint(
            ["emitido_por"], ["usuario.id"], name=op.f("fk_documento_emitido_emitido_por_usuario")
        ),
        sa.ForeignKeyConstraint(
            ["organo_id"], ["organo.id"], name=op.f("fk_documento_emitido_organo_id_organo")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documento_emitido")),
        sa.UniqueConstraint(
            "codigo_verificacion", name=op.f("uq_documento_emitido_codigo_verificacion")
        ),
        sa.UniqueConstraint(
            "requerimiento_id",
            "tipo",
            "ultima_firma_id",
            name=op.f("uq_documento_emitido_requerimiento_id_tipo_ultima_firma_id"),
        ),
    )
    op.execute(
        """
        CREATE TRIGGER tg_documento_emitido_inmutable
        BEFORE UPDATE OR DELETE ON documento_emitido
        FOR EACH ROW EXECUTE FUNCTION rechazar_modificacion();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tg_documento_emitido_inmutable ON documento_emitido")
    op.drop_table("documento_emitido")
