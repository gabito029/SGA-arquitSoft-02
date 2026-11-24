"""Errores del módulo de firma, con el ``codigo`` del contrato. Python puro."""

from app.core.errores import Conflicto


class NivelYaRegistrado(Conflicto):
    """La restricción única ``(requerimiento_id, nivel)`` rechazó una segunda firma (RN02)."""

    codigo_por_defecto = "NIVEL_YA_FIRMADO"
    mensaje_por_defecto = "Este nivel del conducto regular ya firmó el requerimiento."
