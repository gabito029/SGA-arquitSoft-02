"""Caché en memoria del proceso con tiempo de vida (research §7).

Solo se usa para datos que casi no cambian (catálogo y estructura orgánica). Con varias
instancias, cada una puede quedar desactualizada como mucho durante el TTL, lo que es aceptable
para estos datos.
"""

import threading
import time
from collections.abc import Callable, Hashable
from typing import Any


class CacheTTL:
    def __init__(self, segundos: float, reloj: Callable[[], float] = time.monotonic) -> None:
        self._segundos = segundos
        self._reloj = reloj
        self._entradas: dict[Hashable, tuple[float, Any]] = {}
        self._candado = threading.Lock()

    def obtener_o_calcular(self, clave: Hashable, calcular: Callable[[], Any]) -> Any:
        ahora = self._reloj()
        with self._candado:
            entrada = self._entradas.get(clave)
            if entrada is not None and entrada[0] > ahora:
                return entrada[1]
        valor = calcular()
        with self._candado:
            self._entradas[clave] = (ahora + self._segundos, valor)
        return valor

    def invalidar(self, clave: Hashable | None = None) -> None:
        """Borra una entrada, o todas si no se indica la clave."""
        with self._candado:
            if clave is None:
                self._entradas.clear()
            else:
                self._entradas.pop(clave, None)
