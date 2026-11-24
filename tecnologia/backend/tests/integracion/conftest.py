"""Fixtures de integración (T034): API + PostgreSQL real (research §9; EQ-03 exige PostgreSQL).

- Base de datos de prueba (``DATABASE_URL_TEST``), creada si no existe, con ``alembic upgrade
  head`` y los seeds.
- Antes de cada prueba se vacían las tablas de negocio con ``TRUNCATE … CASCADE`` y se recarga el
  stock inicial. ``TRUNCATE`` no activa los disparadores por fila de ``UPDATE``/``DELETE``, así
  que no hace falta desactivarlos.
- ``cliente``: ``TestClient`` de FastAPI (httpx).
- ``login(usuario)``: devuelve las cabeceras ``Authorization`` de ese usuario de prueba.
- ``clave_firma``: un par Ed25519 generado en memoria para el firmador real (T059).
"""

import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.engine import Engine

from app.core.config import Configuracion

RAIZ_BACKEND = Path(__file__).resolve().parents[2]
CONTRASENA_PRUEBAS = "Pruebas-SGA-001"


def _url_de_pruebas() -> str:
    url = os.environ.get("DATABASE_URL_TEST") or Configuracion().database_url_test  # type: ignore[call-arg]
    if not url:
        pytest.exit(
            "Falta DATABASE_URL_TEST (en el entorno o en tecnologia/.env) para las pruebas de "
            "integración. Levante PostgreSQL con: docker compose up -d db",
            returncode=2,
        )
    return url


def _clave_en_memoria():
    """Par Ed25519 generado para esta corrida: las pruebas no dependen de la clave del .env."""
    import base64

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    clave = Ed25519PrivateKey.generate()
    pem = clave.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return clave, base64.b64encode(pem).decode("ascii")


# La API y Alembic deben usar la base de datos de prueba: se fija antes de importar la app.
URL_PRUEBAS = _url_de_pruebas()
os.environ["DATABASE_URL"] = URL_PRUEBAS
os.environ["CONTRASENA_DEMO"] = CONTRASENA_PRUEBAS
CLAVE_FIRMA, _PEM_FIRMA = _clave_en_memoria()
os.environ["FIRMA_CLAVE_PRIVADA"] = _PEM_FIRMA
os.environ["FIRMA_CLAVE_ID"] = ""  # se deriva de la clave pública

from app.core import base_datos, config  # noqa: E402

config.obtener_configuracion.cache_clear()
base_datos.obtener_motor.cache_clear()
base_datos.obtener_fabrica_sesiones.cache_clear()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "integracion" in item.path.parts:
            item.add_marker(pytest.mark.integracion)


def _crear_base_si_no_existe(url: str) -> None:
    destino = make_url(url)
    administracion = create_engine(
        destino.set(database="postgres"), isolation_level="AUTOCOMMIT", pool_pre_ping=True
    )
    with administracion.connect() as conexion:
        existe = conexion.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :nombre"),
            {"nombre": destino.database},
        )
        if not existe:
            conexion.execute(text(f'CREATE DATABASE "{destino.database}"'))
    administracion.dispose()


def _migrar(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    configuracion = Config(str(RAIZ_BACKEND / "alembic.ini"))
    configuracion.set_main_option("script_location", str(RAIZ_BACKEND / "migrations"))
    configuracion.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(configuracion, "head")


def _cargar_seeds() -> None:
    from seeds.cargar import cargar

    with base_datos.obtener_fabrica_sesiones()() as sesion, sesion.begin():
        cargar(sesion, CONTRASENA_PRUEBAS)


@pytest.fixture(scope="session")
def motor() -> Iterator[Engine]:
    _crear_base_si_no_existe(URL_PRUEBAS)
    _migrar(URL_PRUEBAS)
    _cargar_seeds()
    # Si la base de datos ya tenía usuarios con otra contraseña, se fija la de las pruebas.
    from app.modules.identity.infraestructura.hash_bcrypt import HasherBcrypt

    with base_datos.obtener_motor().begin() as conexion:
        conexion.execute(
            text("UPDATE usuario SET hash_contrasena = :h"),
            {"h": HasherBcrypt(rondas=4).generar(CONTRASENA_PRUEBAS)},
        )
    yield base_datos.obtener_motor()
    base_datos.obtener_motor().dispose()


TABLAS_DE_NEGOCIO = "requerimiento, registro_auditoria, movimiento, stock"


@pytest.fixture(autouse=True)
def datos_limpios(motor: Engine) -> Iterator[None]:
    """Cada prueba empieza con el catálogo, los usuarios y el stock inicial de los seeds."""
    from app.modules.catalog.infraestructura.dependencias import CACHE_CATALOGO

    with motor.begin() as conexion:
        # CASCADE vacía también item_requerimiento, historial, firma y acta (claves foráneas).
        conexion.execute(text(f"TRUNCATE {TABLAS_DE_NEGOCIO} RESTART IDENTITY CASCADE"))
        conexion.execute(text("UPDATE usuario SET activo = true WHERE NOT activo"))
        conexion.execute(text("UPDATE item SET activo = true WHERE NOT activo"))
    _cargar_seeds()
    CACHE_CATALOGO.invalidar()
    yield


@pytest.fixture
def cliente(motor: Engine):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as cliente_http:
        yield cliente_http


@pytest.fixture
def login(cliente) -> Callable[[str], dict[str, str]]:
    def _login(usuario: str) -> dict[str, str]:
        respuesta = cliente.post(
            "/api/v1/auth/login", json={"usuario": usuario, "contrasena": CONTRASENA_PRUEBAS}
        )
        assert respuesta.status_code == 200, respuesta.text
        return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}

    return _login


@pytest.fixture(scope="session")
def clave_firma():
    """Par Ed25519 en memoria con el que firma la API durante las pruebas (firmador real)."""
    return CLAVE_FIRMA


@pytest.fixture(scope="session")
def firmador(clave_firma):
    from app.modules.signing.infraestructura.firmador_ed25519 import FirmadorEd25519

    return FirmadorEd25519(clave_firma)
