"""Doble de prueba del puerto ``FirmadorDocumentos`` (T059, principio de Liskov).

Cumple el mismo contrato que ``FirmadorEd25519`` sin criptografía asimétrica: la "firma" es un
SHA-256 de una clave fija más el contenido. Sirve para probar los casos de uso sin claves reales.
"""

import base64
import hashlib


class FirmadorFalso:
    metodo = "falso-sha256-v1"

    def __init__(self, clave_id: str = "falso-1", secreto: bytes = b"secreto-de-prueba") -> None:
        self.clave_id = clave_id
        self._secreto = secreto

    def _firma(self, contenido: bytes) -> str:
        return base64.b64encode(hashlib.sha256(self._secreto + contenido).digest()).decode()

    def firmar(self, contenido: bytes) -> str:
        return self._firma(contenido)

    def verificar(self, contenido: bytes, firma: str, clave_id: str) -> bool:
        return clave_id == self.clave_id and firma == self._firma(contenido)
