"""Adaptador de hash de contraseñas con bcrypt (research §4; constitución, principio X)."""

from functools import cache

import bcrypt

# bcrypt solo usa los primeros 72 bytes; se recorta explícitamente para no depender de la versión.
_MAX_BYTES = 72
RONDAS = 12


def _a_bytes(contrasena: str) -> bytes:
    return contrasena.encode("utf-8")[:_MAX_BYTES]


@cache
def _hash_relleno(rondas: int) -> bytes:
    """Hash real de un valor aleatorio, para verificar contra él cuando el usuario no existe."""
    return bcrypt.hashpw(bcrypt.gensalt(rondas), bcrypt.gensalt(rondas))


class HasherBcrypt:
    def __init__(self, rondas: int = RONDAS) -> None:
        self._rondas = rondas

    def generar(self, contrasena: str) -> str:
        return bcrypt.hashpw(_a_bytes(contrasena), bcrypt.gensalt(self._rondas)).decode("ascii")

    def verificar(self, contrasena: str, hash_guardado: str | None) -> bool:
        if hash_guardado is None:
            bcrypt.checkpw(_a_bytes(contrasena), _hash_relleno(self._rondas))
            return False
        try:
            return bcrypt.checkpw(_a_bytes(contrasena), hash_guardado.encode("ascii"))
        except ValueError:
            return False
