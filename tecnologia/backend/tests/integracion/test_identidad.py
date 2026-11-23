"""T035: inicio de sesión, perfil, salud, documentación OpenAPI y catálogo (EQ-01, parte base)."""

import uuid

from sqlalchemy import text

from app.core.seguridad import crear_token
from tests.integracion.conftest import CONTRASENA_PRUEBAS


def _login(cliente, usuario: str, contrasena: str = CONTRASENA_PRUEBAS):
    return cliente.post("/api/v1/auth/login", json={"usuario": usuario, "contrasena": contrasena})


# --- Inicio de sesión ---


def test_inicio_de_sesion_correcto_devuelve_token_y_perfil(cliente):
    respuesta = _login(cliente, "oficial.bim11")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["expira_en"] == 3600
    assert cuerpo["access_token"]
    usuario = cuerpo["usuario"]
    assert usuario["usuario"] == "oficial.bim11"
    assert usuario["rol"] == "OFICIAL_LOGISTICA"
    assert usuario["organo"]["codigo"] == "BIM-11"
    assert usuario["almacen_id"] is None
    assert "hash_contrasena" not in usuario


def test_el_perfil_de_almacen_incluye_su_almacen(cliente):
    usuario = _login(cliente, "almacenero.sinte").json()["usuario"]
    assert usuario["rol"] == "ALMACENERO"
    assert usuario["almacen_id"] is not None


def test_contrasena_incorrecta_da_401_con_mensaje_en_espanol(cliente):
    respuesta = _login(cliente, "oficial.bim11", "incorrecta")
    assert respuesta.status_code == 401
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "NO_AUTENTICADO"
    assert cuerpo["mensaje"] == "Usuario o contraseña incorrectos."
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


def test_usuario_inexistente_da_el_mismo_401(cliente):
    respuesta = _login(cliente, "no.existe")
    assert respuesta.status_code == 401
    assert respuesta.json()["mensaje"] == "Usuario o contraseña incorrectos."


def test_usuario_inactivo_no_puede_iniciar_sesion(cliente, motor):
    with motor.begin() as conexion:
        conexion.execute(text("UPDATE usuario SET activo = false WHERE usuario = 'cmdte.bim11'"))
    assert _login(cliente, "cmdte.bim11").status_code == 401


def test_datos_incompletos_dan_422_con_detalle_por_campo(cliente):
    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": "oficial.bim11"})
    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "VALIDACION"
    assert {"campo": "contrasena", "mensaje": "Este campo es obligatorio."} in cuerpo["detalles"]


# --- /auth/me ---


def test_me_con_token_devuelve_el_usuario(cliente, login):
    respuesta = cliente.get("/api/v1/auth/me", headers=login("jlog.1de"))
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == "JEFE_LOGISTICA_GU"
    assert cuerpo["organo"]["codigo"] == "1DE"


def test_me_sin_token_da_401(cliente):
    respuesta = cliente.get("/api/v1/auth/me")
    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "NO_AUTENTICADO"


def test_me_con_token_invalido_da_401(cliente):
    respuesta = cliente.get("/api/v1/auth/me", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert respuesta.status_code == 401


def test_token_expirado_da_401(cliente):
    usuario_id = cliente.post(
        "/api/v1/auth/login", json={"usuario": "oficial.bim11", "contrasena": CONTRASENA_PRUEBAS}
    ).json()["usuario"]["id"]
    vencido = crear_token(
        usuario_id=uuid.UUID(usuario_id),
        rol="OFICIAL_LOGISTICA",
        organo_id=uuid.uuid4(),
        almacen_id=None,
        minutos=-1,
    )
    respuesta = cliente.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {vencido.token}"})
    assert respuesta.status_code == 401
    assert "expiró" in respuesta.json()["mensaje"]


def test_token_de_un_usuario_desactivado_ya_no_sirve(cliente, login, motor):
    cabeceras = login("oficial.bim12")
    with motor.begin() as conexion:
        conexion.execute(text("UPDATE usuario SET activo = false WHERE usuario = 'oficial.bim12'"))
    assert cliente.get("/api/v1/auth/me", headers=cabeceras).status_code == 401


# --- Salud y documentación (principio IV, ADR-013) ---


def test_health_responde_ok(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "OK", "base_datos": "OK"}


def test_swagger_y_openapi_estan_disponibles(cliente):
    assert cliente.get("/docs").status_code == 200
    especificacion = cliente.get("/openapi.json")
    assert especificacion.status_code == 200
    rutas = especificacion.json()["paths"]
    assert {"/health", "/api/v1/auth/login", "/api/v1/auth/me", "/api/v1/catalogo/items"} <= set(
        rutas
    )


def test_ruta_inexistente_responde_con_el_esquema_error(cliente):
    respuesta = cliente.get("/api/v1/no-existe")
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "NO_ENCONTRADO"


# --- Catálogo (research §7) ---


def test_catalogo_sin_token_da_401(cliente):
    assert cliente.get("/api/v1/catalogo/items").status_code == 401


def test_catalogo_lista_items_activos_con_cache_control(cliente, login):
    respuesta = cliente.get("/api/v1/catalogo/items", headers=login("oficial.bim11"))
    assert respuesta.status_code == 200
    assert respuesta.headers["Cache-Control"] == "private, max-age=300"
    items = respuesta.json()
    assert len(items) == 14
    racion = next(i for i in items if i["codigo"] == "INT-001")
    assert racion["valor_unitario"] == "35.50"
    assert racion["categoria"] == "INTENDENCIA"


def test_catalogo_filtra_por_categoria(cliente, login):
    cabeceras = login("oficial.bim11")
    intendencia = cliente.get(
        "/api/v1/catalogo/items", params={"categoria": "INTENDENCIA"}, headers=cabeceras
    ).json()
    guerra = cliente.get(
        "/api/v1/catalogo/items", params={"categoria": "MATERIAL_GUERRA"}, headers=cabeceras
    ).json()
    assert len(intendencia) == 10
    assert len(guerra) == 4
    assert {i["categoria"] for i in guerra} == {"MATERIAL_GUERRA"}


def test_catalogo_rechaza_una_categoria_invalida(cliente, login):
    respuesta = cliente.get(
        "/api/v1/catalogo/items", params={"categoria": "OTRA"}, headers=login("oficial.bim11")
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == "categoria"


def test_catalogo_no_muestra_items_inactivos(cliente, login, motor):
    with motor.begin() as conexion:
        conexion.execute(text("UPDATE item SET activo = false WHERE codigo = 'INT-010'"))
    try:
        items = cliente.get("/api/v1/catalogo/items", headers=login("oficial.bim11")).json()
        assert "INT-010" not in {i["codigo"] for i in items}
    finally:
        with motor.begin() as conexion:
            conexion.execute(text("UPDATE item SET activo = true WHERE codigo = 'INT-010'"))
