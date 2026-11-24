"""Genera un par de claves Ed25519 para la firma del sistema (ADR-004) e imprime las variables
de entorno ``FIRMA_CLAVE_PRIVADA`` (PEM PKCS#8 en base64) y ``FIRMA_CLAVE_ID``.

Uso (desde tecnologia/)::

    python backend/scripts/generar_clave_firma.py >> .env

La clave privada es un secreto: nunca se versiona (constitución, principio X).
"""

import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generar() -> tuple[str, str]:
    clave = Ed25519PrivateKey.generate()
    pem = clave.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    publica = clave.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    # El identificador deriva de la clave pública: permite saber con qué clave se firmó.
    clave_id = "ed25519-" + hashlib.sha256(publica).hexdigest()[:16]
    return base64.b64encode(pem).decode("ascii"), clave_id


def main() -> None:
    privada, clave_id = generar()
    print(f"FIRMA_CLAVE_PRIVADA={privada}")
    print(f"FIRMA_CLAVE_ID={clave_id}")


if __name__ == "__main__":
    main()
