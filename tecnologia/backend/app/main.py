"""Raíz de composición de la API del SGA (monolito modular, ADR-001).

Crea la aplicación FastAPI, registra los routers de cada módulo y los manejadores de errores.
La documentación OpenAPI queda en /docs (Swagger UI) y /openapi.json (constitución, principio IV).
"""

from fastapi import FastAPI

from app.core.manejadores_errores import registrar_manejadores
from app.core.salud import router as router_salud
from app.modules.catalog.presentacion.router import router as router_catalogo
from app.modules.identity.presentacion.router import router as router_identidad
from app.modules.requests.presentacion.router import router as router_requerimientos

DESCRIPCION = (
    "API REST del flujo principal de abastecimiento (incremento 001). Todos los endpoints, "
    "salvo /health y /api/v1/auth/login, requieren un token JWT: inicie sesión y use "
    "**Authorize** con el `access_token`. En este incremento el entorno local usa HTTP "
    "(desviación temporal DT-02)."
)


def crear_app() -> FastAPI:
    app = FastAPI(
        title="SGA — API del flujo principal de abastecimiento (incremento 001)",
        version="0.1.0",
        description=DESCRIPCION,
    )
    registrar_manejadores(app)
    app.include_router(router_salud)
    app.include_router(router_identidad)
    app.include_router(router_catalogo)
    app.include_router(router_requerimientos)
    return app


app = crear_app()
