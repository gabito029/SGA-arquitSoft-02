"""Regla de dependencia (constitución, principio V): el dominio no importa FastAPI, SQLAlchemy
ni ``cryptography``, y ningún módulo usa las tablas o el repositorio de otro."""

import ast
from pathlib import Path

import pytest

RAIZ_MODULOS = Path(__file__).resolve().parents[2] / "app" / "modules"
PROHIBIDOS_EN_DOMINIO = ("fastapi", "sqlalchemy", "cryptography", "starlette", "jwt", "bcrypt")


def _importaciones(archivo: Path) -> list[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.append(nodo.module)
    return nombres


ARCHIVOS_DOMINIO = sorted(RAIZ_MODULOS.glob("*/dominio/*.py"))
ARCHIVOS_MODULOS = sorted(RAIZ_MODULOS.glob("*/*/*.py"))


@pytest.mark.parametrize(
    "archivo", ARCHIVOS_DOMINIO, ids=lambda p: f"{p.parent.parent.name}/{p.name}"
)
def test_el_dominio_es_python_puro(archivo: Path):
    prohibidas = [m for m in _importaciones(archivo) if m.split(".")[0] in PROHIBIDOS_EN_DOMINIO]
    assert prohibidas == [], f"{archivo} importa {prohibidas}"


@pytest.mark.parametrize(
    "archivo", ARCHIVOS_MODULOS, ids=lambda p: f"{p.parent.parent.name}/{p.parent.name}/{p.name}"
)
def test_un_modulo_no_usa_la_infraestructura_de_otro(archivo: Path):
    modulo = archivo.parent.parent.name
    ajenas = []
    for importado in _importaciones(archivo):
        partes = importado.split(".")
        if partes[:2] == ["app", "modules"] and len(partes) >= 4:
            otro, capa = partes[2], partes[3]
            # Se permiten los tipos del dominio y los servicios públicos (aplicación) de otros
            # módulos, y la composición de sus adaptadores (``dependencias``).
            es_composicion = capa == "infraestructura" and partes[-1] == "dependencias"
            if otro != modulo and capa == "infraestructura" and not es_composicion:
                ajenas.append(importado)
    assert ajenas == [], f"{archivo} usa infraestructura de otro módulo: {ajenas}"
