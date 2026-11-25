"""Errores del módulo de firma, con el ``codigo`` del contrato. Python puro."""

from app.core.errores import Conflicto, NoEncontrado


class NivelYaRegistrado(Conflicto):
    """La restricción única ``(requerimiento_id, nivel)`` rechazó una segunda firma (RN02)."""

    codigo_por_defecto = "NIVEL_YA_FIRMADO"
    mensaje_por_defecto = "Este nivel del conducto regular ya firmó el requerimiento."


class DocumentoExistente(Conflicto):
    """El documento ya fue emitido o el archivo ya existe: los PDF no se sobrescriben (ADR-010)."""

    codigo_por_defecto = "DOCUMENTO_EXISTENTE"
    mensaje_por_defecto = "El documento ya fue emitido."


class DocumentoNoEncontrado(NoEncontrado):
    codigo_por_defecto = "DOCUMENTO_NO_ENCONTRADO"
    mensaje_por_defecto = "El documento guardado no existe."


class DocumentoInconsistente(Conflicto):
    """El archivo guardado no coincide con su huella registrada (FR-013): no se entrega."""

    codigo_por_defecto = "DOCUMENTO_INCONSISTENTE"
    mensaje_por_defecto = (
        "El documento guardado no coincide con su huella registrada; no se puede entregar."
    )
