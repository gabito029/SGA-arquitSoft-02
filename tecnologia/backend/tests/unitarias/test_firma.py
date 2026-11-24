"""T055 — Firma digital (EQ-02, parte unitaria; ADR-004, research §3).

- El contenido canónico es estable aunque cambie el orden de las claves o de los ítems.
- Firmar y verificar con Ed25519 da INTEGRA; cambiar un byte del contenido o de la firma da
  ALTERADA.
- Se guardan ``metodo`` y ``clave_id``.
"""

import base64
import uuid
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.modules.signing.aplicacion.servicio_firma import ServicioFirma
from app.modules.signing.dominio.contenido_canonico import (
    DocumentoFirmable,
    Firmante,
    LineaFirmable,
    contenido_de_nivel,
    huella_sha256,
    serializar,
)
from app.modules.signing.dominio.errores import NivelYaRegistrado
from app.modules.signing.dominio.puertos import FirmaRegistrada
from app.modules.signing.dominio.tipos import DecisionFirma, NivelFirma, ResultadoVerificacion
from app.modules.signing.infraestructura.firmador_ed25519 import (
    METODO,
    FirmadorEd25519,
    clave_id_de,
)
from tests.firmador_falso import FirmadorFalso

ITEM_A, ITEM_B = uuid.UUID(int=1), uuid.UUID(int=2)
FECHA = datetime(2026, 11, 24, 15, 30, 0, 123456, tzinfo=UTC)
FIRMANTE = Firmante(id=uuid.uuid4(), rol="COMANDANTE_UNIDAD", organo_id=uuid.uuid4())


def documento(*lineas: LineaFirmable) -> DocumentoFirmable:
    return DocumentoFirmable(
        id=uuid.UUID(int=99),
        codigo="REQ-2026-000001",
        unidad_id=uuid.UUID(int=7),
        categoria="INTENDENCIA",
        items=lineas or (LineaFirmable(ITEM_A, 10), LineaFirmable(ITEM_B, 5)),
    )


class RepositorioEnMemoria:
    def __init__(self) -> None:
        self.firmas: list[FirmaRegistrada] = []

    def guardar(self, firma: FirmaRegistrada) -> None:
        if any(
            f.requerimiento_id == firma.requerimiento_id and f.nivel == firma.nivel
            for f in self.firmas
        ):
            raise NivelYaRegistrado()
        self.firmas.append(firma)

    def listar(self, requerimiento_id: uuid.UUID) -> list[FirmaRegistrada]:
        return [f for f in self.firmas if f.requerimiento_id == requerimiento_id]

    def niveles(self, requerimiento_id: uuid.UUID) -> set[NivelFirma]:
        return {f.nivel for f in self.listar(requerimiento_id)}


@pytest.fixture
def firmador() -> FirmadorEd25519:
    return FirmadorEd25519(Ed25519PrivateKey.generate())


@pytest.fixture
def servicio(firmador) -> ServicioFirma:
    return ServicioFirma(RepositorioEnMemoria(), firmador, reloj=lambda: FECHA)


# --- Contenido canónico ---


def test_el_contenido_canonico_no_depende_del_orden_de_las_claves_ni_de_los_items():
    a = serializar(
        contenido_de_nivel(
            documento(), NivelFirma.VB_UNIDAD, DecisionFirma.APROBAR, FIRMANTE, FECHA
        )
    )
    invertido = documento(LineaFirmable(ITEM_B, 5), LineaFirmable(ITEM_A, 10))
    b = serializar(
        contenido_de_nivel(invertido, NivelFirma.VB_UNIDAD, DecisionFirma.APROBAR, FIRMANTE, FECHA)
    )
    assert a == b
    assert serializar({"b": 1, "a": {"y": 2, "x": 1}}) == serializar(
        {"a": {"x": 1, "y": 2}, "b": 1}
    )
    assert serializar({"b": 1, "a": 2}) == b'{"a":2,"b":1}'  # compacto, sin espacios


def test_los_niveles_previos_no_firman_estado_version_ni_cantidades_posteriores():
    contenido = contenido_de_nivel(
        documento(LineaFirmable(ITEM_A, 10, cantidad_despachada=7, cantidad_recibida=7)),
        NivelFirma.CONFORMIDAD_GU,
        DecisionFirma.APROBAR,
        FIRMANTE,
        FECHA,
    )
    texto = serializar(contenido).decode()
    for campo in ("estado", "version", "cantidad_despachada", "cantidad_recibida"):
        assert campo not in texto
    # El despacho no cambia el contenido del visto bueno: la firma anterior sigue íntegra.
    sin_despacho = contenido_de_nivel(
        documento(LineaFirmable(ITEM_A, 10)),
        NivelFirma.CONFORMIDAD_GU,
        DecisionFirma.APROBAR,
        FIRMANTE,
        FECHA,
    )
    assert serializar(contenido) == serializar(sin_despacho)


def test_el_acta_firma_lo_despachado_lo_recibido_y_las_observaciones():
    contenido = contenido_de_nivel(
        documento(LineaFirmable(ITEM_A, 10, 7, 6, "Una caja dañada")),
        NivelFirma.ACTA_RECEPCION,
        DecisionFirma.APROBAR,
        FIRMANTE,
        FECHA,
    )
    item = contenido["requerimiento"]["items"][0]
    assert (item["cantidad_despachada"], item["cantidad_recibida"]) == (7, 6)
    assert item["observacion"] == "Una caja dañada"
    assert "Una caja dañada".encode() in serializar(contenido)  # UTF-8, sin escapes


def test_la_huella_es_sha256_hexadecimal():
    huella = huella_sha256(b"abc")
    assert huella == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# --- Firmar y verificar con Ed25519 ---


def test_firmar_y_verificar_da_integra_y_guarda_metodo_y_clave_id(servicio, firmador):
    firma = servicio.firmar_nivel(
        documento(), NivelFirma.VB_UNIDAD, DecisionFirma.APROBAR, FIRMANTE
    )
    assert firma.metodo == METODO == "ed25519-sha256-v1"
    assert firma.clave_id == firmador.clave_id
    assert firma.clave_id.startswith("ed25519-")
    assert firma.firmado_en == FECHA
    assert len(base64.b64decode(firma.firma)) == 64  # firma Ed25519
    assert firma.huella_sha256 == huella_sha256(firma.contenido_canonico.encode())
    assert servicio.firmas(documento().id) == [firma]
    assert servicio.niveles_firmados(documento().id) == {NivelFirma.VB_UNIDAD}
    assert servicio.verificar(firma, documento()) is ResultadoVerificacion.INTEGRA


def test_cambiar_un_dato_firmado_da_alterada(servicio):
    firma = servicio.firmar_nivel(
        documento(), NivelFirma.VB_UNIDAD, DecisionFirma.APROBAR, FIRMANTE
    )
    alterado = documento(LineaFirmable(ITEM_A, 11), LineaFirmable(ITEM_B, 5))
    assert servicio.verificar(firma, alterado) is ResultadoVerificacion.ALTERADA


def test_cambiar_un_byte_del_contenido_o_de_la_firma_da_alterada(firmador):
    contenido = serializar(
        contenido_de_nivel(
            documento(), NivelFirma.VB_UNIDAD, DecisionFirma.APROBAR, FIRMANTE, FECHA
        )
    )
    firma = firmador.firmar(contenido)
    assert firmador.verificar(contenido, firma, firmador.clave_id)

    contenido_alterado = bytearray(contenido)
    contenido_alterado[10] ^= 0x01
    assert not firmador.verificar(bytes(contenido_alterado), firma, firmador.clave_id)

    bytes_firma = bytearray(base64.b64decode(firma))
    bytes_firma[0] ^= 0x01
    firma_alterada = base64.b64encode(bytes(bytes_firma)).decode()
    assert not firmador.verificar(contenido, firma_alterada, firmador.clave_id)
    assert not firmador.verificar(contenido, "no-es-base64!!", firmador.clave_id)


def test_una_firma_alterada_en_el_registro_da_alterada(servicio):
    firma = servicio.firmar_nivel(
        documento(), NivelFirma.VB_UNIDAD, DecisionFirma.APROBAR, FIRMANTE
    )
    bytes_firma = bytearray(base64.b64decode(firma.firma))
    bytes_firma[-1] ^= 0xFF
    otra = FirmaRegistrada(**{**firma.__dict__, "firma": base64.b64encode(bytes_firma).decode()})
    assert servicio.verificar(otra, documento()) is ResultadoVerificacion.ALTERADA


def test_otra_clave_no_verifica(firmador):
    contenido = b"contenido"
    firma = firmador.firmar(contenido)
    otro = FirmadorEd25519(Ed25519PrivateKey.generate())
    assert not otro.verificar(contenido, firma, otro.clave_id)
    assert not firmador.verificar(contenido, firma, "ed25519-otra")


def test_la_clave_se_carga_desde_pem_en_base64():
    from scripts.generar_clave_firma import generar

    privada, clave_id = generar()
    firmador = FirmadorEd25519.desde_pem_base64(privada, clave_id)
    assert firmador.clave_id == clave_id
    assert firmador.verificar(b"x", firmador.firmar(b"x"), clave_id)
    sin_id = FirmadorEd25519.desde_pem_base64(privada)
    assert sin_id.clave_id == clave_id == clave_id_de(sin_id._clave)


def test_sin_clave_configurada_falla_con_un_mensaje_claro():
    with pytest.raises(RuntimeError, match="FIRMA_CLAVE_PRIVADA"):
        FirmadorEd25519.desde_pem_base64("")


def test_un_nivel_no_firma_dos_veces(servicio):
    servicio.firmar_nivel(documento(), NivelFirma.VB_UNIDAD, DecisionFirma.APROBAR, FIRMANTE)
    with pytest.raises(NivelYaRegistrado) as error:
        servicio.firmar_nivel(documento(), NivelFirma.VB_UNIDAD, DecisionFirma.RECHAZAR, FIRMANTE)
    assert error.value.codigo == "NIVEL_YA_FIRMADO"


# --- El doble de prueba cumple el mismo puerto (Liskov) ---


@pytest.mark.parametrize(
    "fabrica", [lambda: FirmadorEd25519(Ed25519PrivateKey.generate()), FirmadorFalso]
)
def test_cualquier_firmador_cumple_el_contrato(fabrica):
    firmador = fabrica()
    servicio = ServicioFirma(RepositorioEnMemoria(), firmador, reloj=lambda: FECHA)
    firma = servicio.firmar_nivel(
        documento(), NivelFirma.APROBACION_ALMACEN, DecisionFirma.RECHAZAR, FIRMANTE
    )
    assert (firma.metodo, firma.clave_id) == (firmador.metodo, firmador.clave_id)
    assert servicio.verificar(firma, documento()) is ResultadoVerificacion.INTEGRA
    assert (
        servicio.verificar(firma, documento(LineaFirmable(ITEM_A, 1)))
        is ResultadoVerificacion.ALTERADA
    )
