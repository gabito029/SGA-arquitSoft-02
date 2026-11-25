"""Implementa ``RepositorioDocumentos`` con SQLAlchemy (tabla ``documento_emitido``, 002).

La fila se inserta dentro de un *savepoint*: si otra petición emitió el mismo estado firmado al
mismo tiempo, el índice único rechaza la inserción, se deshace solo el savepoint y se lanza
``DocumentoExistente``, sin abortar la transacción de la petición.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.signing.dominio.documento import DocumentoEmitido, TipoDocumento
from app.modules.signing.dominio.errores import DocumentoExistente
from app.modules.signing.infraestructura.modelos import DocumentoEmitidoModelo


def _a_dominio(m: DocumentoEmitidoModelo) -> DocumentoEmitido:
    return DocumentoEmitido(
        id=m.id,
        codigo_verificacion=m.codigo_verificacion,
        tipo=TipoDocumento(m.tipo),
        requerimiento_id=m.requerimiento_id,
        ultima_firma_id=m.ultima_firma_id,
        firmas_incluidas=tuple(uuid.UUID(f) for f in m.firmas_incluidas),
        huella_contenido=m.huella_contenido,
        huella_sha256=m.huella_sha256,
        firma=m.firma,
        metodo=m.metodo,
        clave_id=m.clave_id,
        clave_almacen=m.clave_almacen,
        tamano_bytes=m.tamano_bytes,
        emitido_por=m.emitido_por,
        organo_id=m.organo_id,
        emitido_en=m.emitido_en,
    )


class RepositorioDocumentosPostgres:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def buscar(
        self, requerimiento_id: uuid.UUID, tipo: TipoDocumento, ultima_firma_id: uuid.UUID
    ) -> DocumentoEmitido | None:
        fila = self._sesion.scalar(
            select(DocumentoEmitidoModelo).where(
                DocumentoEmitidoModelo.requerimiento_id == requerimiento_id,
                DocumentoEmitidoModelo.tipo == tipo.value,
                DocumentoEmitidoModelo.ultima_firma_id == ultima_firma_id,
            )
        )
        return _a_dominio(fila) if fila else None

    def por_codigo(self, codigo: str) -> DocumentoEmitido | None:
        fila = self._sesion.scalar(
            select(DocumentoEmitidoModelo).where(
                DocumentoEmitidoModelo.codigo_verificacion == codigo
            )
        )
        return _a_dominio(fila) if fila else None

    def guardar(self, documento: DocumentoEmitido) -> None:
        modelo = DocumentoEmitidoModelo(
            id=documento.id,
            codigo_verificacion=documento.codigo_verificacion,
            tipo=documento.tipo.value,
            requerimiento_id=documento.requerimiento_id,
            ultima_firma_id=documento.ultima_firma_id,
            firmas_incluidas=[str(f) for f in documento.firmas_incluidas],
            huella_contenido=documento.huella_contenido,
            huella_sha256=documento.huella_sha256,
            firma=documento.firma,
            metodo=documento.metodo,
            clave_id=documento.clave_id,
            clave_almacen=documento.clave_almacen,
            tamano_bytes=documento.tamano_bytes,
            emitido_por=documento.emitido_por,
            organo_id=documento.organo_id,
            emitido_en=documento.emitido_en,
        )
        try:
            with self._sesion.begin_nested():
                self._sesion.add(modelo)
                self._sesion.flush()
        except IntegrityError as error:
            raise DocumentoExistente() from error
