"""Disparadores de inmutabilidad (research §6; data-model.md §4 → Protección del acta).

- ``firma``, ``acta_recepcion``, ``movimiento``, ``historial_requerimiento`` y
  ``registro_auditoria`` rechazan siempre ``UPDATE`` y ``DELETE``.
- ``requerimiento`` rechaza ``DELETE`` siempre (nada se elimina, principio IX) y ``UPDATE``
  cuando ``OLD.estado`` es final. Se evalúa ``OLD.estado``, no ``NEW.estado``, para no bloquear la
  propia transición a CONFIRMADA, RECHAZADA o ANULADA.
- ``item_requerimiento`` rechaza ``INSERT``, ``UPDATE`` y ``DELETE`` cuando el requerimiento padre
  ya está en un estado final. Por eso el acta escribe los ítems antes de cambiar el estado (T076).

``TRUNCATE`` no activa estos disparadores por fila; las pruebas lo usan para limpiar los datos.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLAS_INMUTABLES = (
    "firma",
    "acta_recepcion",
    "movimiento",
    "historial_requerimiento",
    "registro_auditoria",
)

ESTADOS_FINALES = "('CONFIRMADA', 'RECHAZADA', 'ANULADA')"


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION rechazar_modificacion() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'La tabla % es inmutable: no admite %', TG_TABLE_NAME, TG_OP
                USING ERRCODE = 'restrict_violation';
        END;
        $$;
        """
    )
    for tabla in TABLAS_INMUTABLES:
        op.execute(
            f"""
            CREATE TRIGGER tg_{tabla}_inmutable
            BEFORE UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION rechazar_modificacion();
            """
        )

    op.execute(
        f"""
        CREATE FUNCTION proteger_requerimiento() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Un requerimiento no se elimina; se anula con motivo'
                    USING ERRCODE = 'restrict_violation';
            END IF;
            IF OLD.estado IN {ESTADOS_FINALES} THEN
                RAISE EXCEPTION 'El requerimiento % está en un estado final (%) y es inmutable',
                    OLD.codigo, OLD.estado
                    USING ERRCODE = 'restrict_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER tg_requerimiento_protegido
        BEFORE UPDATE OR DELETE ON requerimiento
        FOR EACH ROW EXECUTE FUNCTION proteger_requerimiento();
        """
    )

    op.execute(
        f"""
        CREATE FUNCTION proteger_item_requerimiento() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            estado_padre estado_requerimiento;
        BEGIN
            SELECT estado INTO estado_padre FROM requerimiento
            WHERE id = COALESCE(NEW.requerimiento_id, OLD.requerimiento_id);
            IF estado_padre IN {ESTADOS_FINALES} THEN
                RAISE EXCEPTION 'Los ítems de un requerimiento en estado final (%) son inmutables',
                    estado_padre
                    USING ERRCODE = 'restrict_violation';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER tg_item_requerimiento_protegido
        BEFORE INSERT OR UPDATE OR DELETE ON item_requerimiento
        FOR EACH ROW EXECUTE FUNCTION proteger_item_requerimiento();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tg_item_requerimiento_protegido ON item_requerimiento")
    op.execute("DROP FUNCTION IF EXISTS proteger_item_requerimiento()")
    op.execute("DROP TRIGGER IF EXISTS tg_requerimiento_protegido ON requerimiento")
    op.execute("DROP FUNCTION IF EXISTS proteger_requerimiento()")
    for tabla in TABLAS_INMUTABLES:
        op.execute(f"DROP TRIGGER IF EXISTS tg_{tabla}_inmutable ON {tabla}")
    op.execute("DROP FUNCTION IF EXISTS rechazar_modificacion()")
