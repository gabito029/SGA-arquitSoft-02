"""Motor, sesiones y base declarativa de SQLAlchemy (ADR-003).

Todos los módulos registran sus tablas en ``Base.metadata``; Alembic la usa para las migraciones.
El motor se crea al primer uso, para que las pruebas puedan fijar ``DATABASE_URL`` antes.
"""

from functools import lru_cache

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import obtener_configuracion

# Nombres de restricciones estables: la migración y los modelos generan los mismos nombres.
CONVENCION_NOMBRES = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)


@lru_cache
def obtener_motor() -> Engine:
    configuracion = obtener_configuracion()
    return create_engine(
        configuracion.database_url,
        pool_size=10,
        max_overflow=10,
        pool_pre_ping=True,
    )


@lru_cache
def obtener_fabrica_sesiones() -> sessionmaker[Session]:
    return sessionmaker(bind=obtener_motor(), autoflush=False, expire_on_commit=False)
