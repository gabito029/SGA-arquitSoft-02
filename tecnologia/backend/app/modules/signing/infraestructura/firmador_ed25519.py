"""Firmador Ed25519 con la librería ``cryptography`` (ADR-004, research §3).

Método ``ed25519-sha256-v1``: se firma la huella SHA-256 del contenido canónico. La clave privada
llega por ``FIRMA_CLAVE_PRIVADA`` (PEM PKCS#8 en base64) y nunca se versiona (principio X).
"""

import base64
import binascii
import hashlib

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

METODO = "ed25519-sha256-v1"


def clave_id_de(clave: Ed25519PrivateKey) -> str:
    publica = clave.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    return "ed25519-" + hashlib.sha256(publica).hexdigest()[:16]


class FirmadorEd25519:
    metodo = METODO

    def __init__(self, clave: Ed25519PrivateKey, clave_id: str | None = None) -> None:
        self._clave = clave
        self._publica = clave.public_key()
        self.clave_id = clave_id or clave_id_de(clave)

    @classmethod
    def desde_pem_base64(cls, pem_base64: str, clave_id: str | None = None) -> "FirmadorEd25519":
        if not pem_base64:
            raise RuntimeError(
                "Falta FIRMA_CLAVE_PRIVADA. Genérela con backend/scripts/generar_clave_firma.py."
            )
        clave = serialization.load_pem_private_key(base64.b64decode(pem_base64), password=None)
        if not isinstance(clave, Ed25519PrivateKey):
            raise RuntimeError("FIRMA_CLAVE_PRIVADA no es una clave Ed25519.")
        return cls(clave, clave_id or None)

    def firmar(self, contenido: bytes) -> str:
        firma = self._clave.sign(hashlib.sha256(contenido).digest())
        return base64.b64encode(firma).decode("ascii")

    def verificar(self, contenido: bytes, firma: str, clave_id: str) -> bool:
        if clave_id != self.clave_id:
            return False
        try:
            self._publica.verify(
                base64.b64decode(firma, validate=True), hashlib.sha256(contenido).digest()
            )
        except (InvalidSignature, binascii.Error, ValueError):
            return False
        return True
