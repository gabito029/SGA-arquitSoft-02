"""Implementa ``AlmacenDocumentos`` en el disco local (ADR-010; research §7 de 002).

En Docker Compose la carpeta raíz es el volumen ``documentos`` (``/datos/documentos``). Los PDF
firmados no se modifican: ``guardar`` nunca sobrescribe (enlace duro exclusivo desde un archivo
temporal, así un archivo a medio escribir nunca queda con su nombre final) y no hay método para
borrar. Las claves se validan para que no salgan de la carpeta raíz.
"""

import os
import uuid
from pathlib import Path, PurePosixPath

from app.modules.signing.dominio.errores import DocumentoExistente, DocumentoNoEncontrado


class AlmacenDocumentosDisco:
    def __init__(self, raiz: str | Path) -> None:
        self._raiz = Path(raiz).resolve()

    def _ruta(self, clave: str) -> Path:
        relativa = PurePosixPath(clave)
        if (
            not clave
            or "\\" in clave
            or relativa.is_absolute()
            or any(parte in ("", ".", "..") for parte in clave.split("/"))
        ):
            raise ValueError(f"Clave de documento no válida: {clave!r}")
        ruta = (self._raiz / Path(*relativa.parts)).resolve()
        if not ruta.is_relative_to(self._raiz):
            raise ValueError(f"Clave de documento fuera del almacenamiento: {clave!r}")
        return ruta

    def guardar(self, clave: str, contenido: bytes) -> None:
        ruta = self._ruta(clave)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if ruta.exists():
            raise DocumentoExistente()
        temporal = ruta.with_name(f".{ruta.name}.{uuid.uuid4().hex}.tmp")
        try:
            with open(temporal, "xb") as archivo:
                archivo.write(contenido)
                archivo.flush()
                os.fsync(archivo.fileno())
            try:
                # Falla si el nombre final ya existe: nunca se sobrescribe un PDF emitido.
                os.link(temporal, ruta)
            except FileExistsError as error:
                raise DocumentoExistente() from error
        finally:
            temporal.unlink(missing_ok=True)

    def leer(self, clave: str) -> bytes:
        try:
            return self._ruta(clave).read_bytes()
        except FileNotFoundError as error:
            raise DocumentoNoEncontrado() from error
