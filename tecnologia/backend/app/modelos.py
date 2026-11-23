"""Registra los modelos de todos los módulos en ``Base.metadata``.

Lo usan Alembic (migrations/env.py) y las pruebas que comparan los modelos con la migración.
"""

from app.core.base_datos import Base
from app.modules.audit.infraestructura import modelos as _audit  # noqa: F401
from app.modules.catalog.infraestructura import modelos as _catalog  # noqa: F401
from app.modules.identity.infraestructura import modelos as _identity  # noqa: F401
from app.modules.inventory.infraestructura import modelos as _inventory  # noqa: F401
from app.modules.requests.infraestructura import modelos as _requests  # noqa: F401
from app.modules.signing.infraestructura import modelos as _signing  # noqa: F401

metadata = Base.metadata
