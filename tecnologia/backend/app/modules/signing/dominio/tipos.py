"""Tipos de la firma digital (data-model.md firma.nivel y firma.decision). Python puro."""

from enum import StrEnum


class NivelFirma(StrEnum):
    VB_UNIDAD = "VB_UNIDAD"
    CONFORMIDAD_GU = "CONFORMIDAD_GU"
    APROBACION_ALMACEN = "APROBACION_ALMACEN"
    ACTA_RECEPCION = "ACTA_RECEPCION"
    # AUTORIZACION_COLOGE llega en el incremento 002.


class DecisionFirma(StrEnum):
    APROBAR = "APROBAR"
    RECHAZAR = "RECHAZAR"


class ResultadoVerificacion(StrEnum):
    """Resultado de verificar las firmas de un requerimiento ("la firma", 001)."""

    INTEGRA = "INTEGRA"
    ALTERADA = "ALTERADA"


class ResultadoPdf(StrEnum):
    """Resultado de verificar un PDF subido ("el documento", literal a EQ-02; 002)."""

    AUTENTICO = "AUTENTICO"
    ALTERADO = "ALTERADO"
