"""Dobles de prueba de los puertos de documentos de 002 (principio de Liskov): cumplen el mismo
contrato que el disco, ReportLab y PostgreSQL, en memoria."""

import uuid

from app.modules.signing.dominio.documento import DocumentoEmitido, DocumentoPdf, TipoDocumento
from app.modules.signing.dominio.errores import DocumentoExistente, DocumentoNoEncontrado


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.archivos: dict[str, bytes] = {}

    def guardar(self, clave: str, contenido: bytes) -> None:
        if clave in self.archivos:
            raise DocumentoExistente()
        self.archivos[clave] = contenido

    def leer(self, clave: str) -> bytes:
        if clave not in self.archivos:
            raise DocumentoNoEncontrado()
        return self.archivos[clave]


class GeneradorFalso:
    """Un "PDF" mínimo con el código en los bytes, como hace ReportLab en los metadatos."""

    def __init__(self) -> None:
        self.generados = 0

    def generar(self, documento: DocumentoPdf, codigo: str, huella_contenido: str) -> bytes:
        self.generados += 1
        return f"%PDF-1.4 {documento.numero} {codigo} {huella_contenido} %%EOF".encode()


class RepositorioDocumentosEnMemoria:
    def __init__(self) -> None:
        self.filas: list[DocumentoEmitido] = []
        # Simula que otra petición guardó la misma emisión justo antes (carrera).
        self.adelantarse: DocumentoEmitido | None = None

    def buscar(
        self, requerimiento_id: uuid.UUID, tipo: TipoDocumento, ultima_firma_id: uuid.UUID
    ) -> DocumentoEmitido | None:
        return next(
            (
                f
                for f in self.filas
                if (f.requerimiento_id, f.tipo, f.ultima_firma_id)
                == (requerimiento_id, tipo, ultima_firma_id)
            ),
            None,
        )

    def por_codigo(self, codigo: str) -> DocumentoEmitido | None:
        return next((f for f in self.filas if f.codigo_verificacion == codigo), None)

    def guardar(self, documento: DocumentoEmitido) -> None:
        if self.adelantarse is not None:
            self.filas.append(self.adelantarse)
            self.adelantarse = None
        if self.buscar(documento.requerimiento_id, documento.tipo, documento.ultima_firma_id):
            raise DocumentoExistente()
        self.filas.append(documento)
