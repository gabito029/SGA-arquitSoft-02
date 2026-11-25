"""Endpoints de requerimientos (contracts/openapi.yaml → /api/v1/requerimientos).

Cada petición abre una Unidad de Trabajo: o se guarda todo (estado, ítems, historial, auditoría)
o no se guarda nada (ADR-003).
"""

import uuid

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.seguridad import UsuarioActual, requiere_rol, usuario_actual
from app.core.unidad_trabajo import FabricaUnidadTrabajo, obtener_fabrica_uow
from app.modules.identity.dominio.rol import Rol
from app.modules.requests.aplicacion.consultar_requerimientos import TAMANO_MAXIMO_PAGINA
from app.modules.requests.aplicacion.politica_acceso import Actor
from app.modules.requests.dominio.estado import EstadoRequerimiento
from app.modules.requests.infraestructura.dependencias import (
    construir_anular,
    construir_confirmar_recepcion,
    construir_consultar,
    construir_consultar_acta,
    construir_consultar_documento,
    construir_consultar_firmas,
    construir_consultar_historial,
    construir_descargar_pdf,
    construir_despachar,
    construir_enviar,
    construir_firmar,
    construir_registrar,
    construir_verificar,
)
from app.modules.requests.presentacion.esquemas import (
    ActaEntrada,
    ActaSalida,
    DecisionFirmaEntrada,
    DespachoEntrada,
    DocumentoSalida,
    EntradaHistorialSalida,
    FirmaSalida,
    MotivoEntrada,
    PaginaRequerimientosSalida,
    RequerimientoEntrada,
    RequerimientoSalida,
    VerificacionSalida,
)
from app.modules.signing.dominio.documento import TipoDocumento

router = APIRouter(prefix="/api/v1/requerimientos", tags=["Requerimientos"])

solo_oficial = requiere_rol(Rol.OFICIAL_LOGISTICA)
solo_firmantes = requiere_rol(Rol.COMANDANTE_UNIDAD, Rol.JEFE_LOGISTICA_GU, Rol.JEFE_ALMACEN)
solo_almacenero = requiere_rol(Rol.ALMACENERO)

_R401 = {401: {"description": "Sin sesión o token inválido/expirado"}}
_R403 = {403: {"description": "El rol del usuario no puede realizar esta acción"}}
_R404 = {404: {"description": "No existe o no pertenece a la jurisdicción del usuario"}}
_R409 = {
    409: {
        "description": "Regla de negocio: TRANSICION_NO_PERMITIDA, NIVEL_YA_FIRMADO, "
        "REQUIERE_COLOGE (envío bloqueado; queda ENVIO_BLOQUEADO en el historial) o "
        "ESTADO_CAMBIADO (acción concurrente)"
    }
}
_R422 = {422: {"description": "Datos de entrada inválidos (indica el campo y el motivo)"}}


def _actor(usuario: UsuarioActual) -> Actor:
    return Actor(
        id=usuario.id,
        rol=Rol(usuario.rol),
        organo_id=usuario.organo_id,
        almacen_id=usuario.almacen_id,
    )


@router.get(
    "",
    response_model=PaginaRequerimientosSalida,
    summary="Bandeja de requerimientos visibles para el usuario según su rol y órgano "
    "(FR-002, FR-029)",
    description="Aplica la visibilidad por rol de data-model.md §7. Los requerimientos en "
    "BORRADOR solo los ven los oficiales de logística de su unidad.",
    responses={**_R401, **_R422},
)
def listar(
    estado: EstadoRequerimiento | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=TAMANO_MAXIMO_PAGINA),
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> PaginaRequerimientosSalida:
    with fabrica_uow() as uow:
        pagina = construir_consultar(uow.sesion).bandeja(
            _actor(usuario), estado=estado, page=page, size=size
        )
    return PaginaRequerimientosSalida.desde_pagina(pagina)


@router.post(
    "",
    response_model=RequerimientoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un requerimiento en BORRADOR (HU02, RF02)",
    description="Solo OFICIAL_LOGISTICA. La unidad y el almacén se deducen del usuario y de la "
    "categoría de los ítems.",
    responses={**_R401, **_R403, **_R422},
)
def registrar(
    entrada: RequerimientoEntrada,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        req = construir_registrar(uow.sesion).registrar(actor, entrada.a_lineas())
        vista = construir_consultar(uow.sesion).detalle(actor, req.id)
    return RequerimientoSalida.desde_vista(vista)


@router.get(
    "/{id}",
    response_model=RequerimientoSalida,
    summary="Detalle del requerimiento con ítems y acciones disponibles para el usuario",
    responses={**_R401, **_R404},
)
def detalle(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    with fabrica_uow() as uow:
        vista = construir_consultar(uow.sesion).detalle(_actor(usuario), id)
    return RequerimientoSalida.desde_vista(vista)


@router.put(
    "/{id}",
    response_model=RequerimientoSalida,
    summary="Editar los ítems de un requerimiento en BORRADOR (FR-008)",
    responses={**_R401, **_R403, **_R404, **_R409, **_R422},
)
def editar(
    id: uuid.UUID,
    entrada: RequerimientoEntrada,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_registrar(uow.sesion).editar(actor, id, entrada.a_lineas())
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)


@router.post(
    "/{id}/enviar",
    response_model=RequerimientoSalida,
    summary="Enviar por el conducto regular (BORRADOR → PENDIENTE_VB_UNIDAD)",
    description="Aplica RN03. Si es de material de guerra o el monto alcanza el umbral, responde "
    "409 con codigo REQUIERE_COLOGE, registra ENVIO_BLOQUEADO en el historial y el estado no "
    "cambia (FR-012).",
    responses={**_R401, **_R403, **_R404, **_R409},
)
def enviar(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_enviar(uow).ejecutar(actor, id)
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)


# --- Firmas del conducto regular (US2) ---


@router.get(
    "/{id}/firmas",
    response_model=list[FirmaSalida],
    tags=["Firmas"],
    summary="Firmas registradas del requerimiento",
    responses={**_R401, **_R404},
)
def listar_firmas(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> list[FirmaSalida]:
    with fabrica_uow() as uow:
        vistas = construir_consultar_firmas(uow.sesion).ejecutar(_actor(usuario), id)
    return [FirmaSalida.desde_vista(v) for v in vistas]


@router.post(
    "/{id}/firmas",
    response_model=RequerimientoSalida,
    status_code=status.HTTP_201_CREATED,
    tags=["Firmas"],
    summary="Firmar (aprobar) o rechazar en el nivel actual del conducto regular "
    "(HU03, HU05, RF03, RF05)",
    description="El nivel se deduce del estado actual; el rol y el órgano del usuario deben "
    "corresponder a ese nivel. Rechazar exige motivo. Un nivel que ya firmó responde 409 "
    "NIVEL_YA_FIRMADO; un estado que no corresponde, 409 TRANSICION_NO_PERMITIDA; y una acción "
    "concurrente que llegó tarde, 409 ESTADO_CAMBIADO.",
    responses={**_R401, **_R403, **_R404, **_R409, **_R422},
)
def firmar(
    id: uuid.UUID,
    entrada: DecisionFirmaEntrada,
    usuario: UsuarioActual = Depends(solo_firmantes),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_firmar(uow.sesion).ejecutar(actor, id, entrada.decision, entrada.motivo)
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)


# --- Despacho (US3) ---


@router.post(
    "/{id}/despacho",
    response_model=RequerimientoSalida,
    status_code=status.HTTP_201_CREATED,
    tags=["Inventario"],
    summary="Despachar un requerimiento APROBADO y descontar el stock (HU07, RF06)",
    description="Solo ALMACENERO del almacén destino. Cantidad ≤ solicitada y ≤ stock. Una sola "
    "transacción con bloqueo del stock (ADR-003). Stock insuficiente → 409 STOCK_INSUFICIENTE.",
    responses={**_R401, **_R403, **_R404, **_R409, **_R422},
)
def despachar(
    id: uuid.UUID,
    entrada: DespachoEntrada,
    usuario: UsuarioActual = Depends(solo_almacenero),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_despachar(uow.sesion).ejecutar(actor, id, entrada.a_cantidades())
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)


# --- Acta de recepción y verificación (US4) ---


@router.post(
    "/{id}/acta",
    response_model=ActaSalida,
    status_code=status.HTTP_201_CREATED,
    tags=["Firmas"],
    summary="Firmar el acta de recepción (HU08, RF07)",
    description="Solo OFICIAL_LOGISTICA de la unidad solicitante, con el requerimiento "
    "EN_TRANSITO. Registra lo recibido y las diferencias, firma con Ed25519 y deja el acta "
    "inmutable; el requerimiento pasa a CONFIRMADA.",
    responses={**_R401, **_R403, **_R404, **_R409, **_R422},
)
def firmar_acta(
    id: uuid.UUID,
    entrada: ActaEntrada,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> ActaSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_confirmar_recepcion(uow.sesion).ejecutar(actor, id, entrada.a_recepcion())
        vista = construir_consultar_acta(uow.sesion).ejecutar(actor, id)
    return ActaSalida.desde_vista(vista)


@router.get(
    "/{id}/acta",
    response_model=ActaSalida,
    tags=["Firmas"],
    summary="Consultar el acta de recepción",
    responses={**_R401, **_R404},
)
def consultar_acta(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> ActaSalida:
    with fabrica_uow() as uow:
        vista = construir_consultar_acta(uow.sesion).ejecutar(_actor(usuario), id)
    return ActaSalida.desde_vista(vista)


@router.get(
    "/{id}/verificacion",
    response_model=VerificacionSalida,
    tags=["Firmas"],
    summary="Verificar la integridad de cada firma y del acta (FR-024, FR-025, EQ-02)",
    description="Reconstruye el contenido canónico de cada firma con los datos actuales y los "
    "campos fijos de su nivel (research §3; nunca estado ni version) y responde INTEGRA o "
    "ALTERADA. Desde el incremento 002 el PDF emitido también se verifica con "
    "POST /api/v1/documentos/verificacion (AUTENTICO o ALTERADO; DT-01 cerrada en v1.3.0).",
    responses={**_R401, **_R404},
)
def verificar(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> VerificacionSalida:
    with fabrica_uow() as uow:
        vista = construir_verificar(uow.sesion).ejecutar(_actor(usuario), id)
    return VerificacionSalida.desde_vista(vista)


# --- Documento oficial (incremento 002, US1 y US4) ---


@router.get(
    "/{id}/documento",
    response_model=DocumentoSalida,
    tags=["Documentos"],
    summary="Documento oficial del requerimiento: encabezado, ítems y sellos (FR-001 a FR-004)",
    description="Los mismos datos que imprime el PDF. Lleva los sellos del conducto regular; el "
    "del acta va en /{id}/acta/documento. Lo ajeno responde 404.",
    responses={**_R401, **_R404},
)
def documento(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> DocumentoSalida:
    with fabrica_uow() as uow:
        vista = construir_consultar_documento(uow.sesion).ejecutar(_actor(usuario), id)
    return DocumentoSalida.desde_vista(vista)


_R409_PDF = {
    409: {
        "description": "SIN_FIRMAS (todavía no hay un documento firmado) o "
        "DOCUMENTO_INCONSISTENTE (el archivo guardado no coincide con su huella; no se entrega)"
    }
}
_RESPUESTA_PDF = {
    200: {
        "content": {"application/pdf": {}},
        "description": "El PDF emitido, con la cabecera X-Codigo-Verificacion",
    }
}


def _respuesta_pdf(pdf) -> Response:
    return Response(
        content=pdf.contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{pdf.nombre_archivo}"',
            "X-Codigo-Verificacion": pdf.codigo_verificacion,
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/{id}/documento.pdf",
    response_class=Response,
    tags=["Documentos"],
    summary="Descargar el PDF firmado del requerimiento (002, FR-008 a FR-013)",
    description="Se emite en la primera descarga después de una firma nueva: huella SHA-256 de "
    "los bytes firmada con Ed25519 y archivo guardado sin cambios (ADR-004, ADR-010). Mientras "
    "no haya firmas nuevas devuelve el mismo PDF.",
    responses={**_RESPUESTA_PDF, **_R401, **_R404, **_R409_PDF},
)
def documento_pdf(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> Response:
    with fabrica_uow() as uow:
        pdf = construir_descargar_pdf(uow.sesion).ejecutar(_actor(usuario), id)
    return _respuesta_pdf(pdf)


@router.get(
    "/{id}/acta/documento",
    response_model=DocumentoSalida,
    tags=["Documentos"],
    summary="Documento del acta de recepción: despachado, recibido y observaciones (002, US4)",
    description="Mismo contrato Documento con tipo ACTA: cada línea trae lo despachado, lo "
    "recibido y la observación, más tiene_diferencias y el sello ACTA_RECEPCION. Sin acta o "
    "ajena responde 404.",
    responses={**_R401, **_R404},
)
def documento_acta(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> DocumentoSalida:
    with fabrica_uow() as uow:
        vista = construir_consultar_documento(uow.sesion).ejecutar(
            _actor(usuario), id, TipoDocumento.ACTA
        )
    return DocumentoSalida.desde_vista(vista)


@router.get(
    "/{id}/acta/documento.pdf",
    response_class=Response,
    tags=["Documentos"],
    summary="Descargar el PDF firmado del acta de recepción (002, US4)",
    description="PDF propio del acta, con su código de verificación distinto del PDF del "
    "requerimiento. Firmar el acta no cambia el PDF del requerimiento.",
    responses={**_RESPUESTA_PDF, **_R401, **_R404, **_R409_PDF},
)
def documento_acta_pdf(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> Response:
    with fabrica_uow() as uow:
        pdf = construir_descargar_pdf(uow.sesion).ejecutar(_actor(usuario), id, TipoDocumento.ACTA)
    return _respuesta_pdf(pdf)


# --- Línea de tiempo (US5) ---


@router.get(
    "/{id}/historial",
    response_model=list[EntradaHistorialSalida],
    summary="Línea de tiempo del requerimiento (RF08, FR-028)",
    description="Entradas en orden cronológico con acción, usuario, rol, órgano, fecha y hora, "
    "estado anterior y motivo. El historial es de solo lectura: no hay endpoints para editarlo "
    "o borrarlo, y la base de datos rechaza UPDATE y DELETE (EQ-08).",
    responses={**_R401, **_R404},
)
def historial(
    id: uuid.UUID,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> list[EntradaHistorialSalida]:
    with fabrica_uow() as uow:
        vistas = construir_consultar_historial(uow.sesion).ejecutar(_actor(usuario), id)
    return [EntradaHistorialSalida.desde_vista(v) for v in vistas]


# --- Anulación (US6) ---


@router.post(
    "/{id}/anular",
    response_model=RequerimientoSalida,
    summary="Anular con motivo, solo desde BORRADOR (FR-022)",
    description="Solo OFICIAL_LOGISTICA de la unidad. La solicitud no se borra: queda ANULADA con "
    "el motivo en el historial. Desde cualquier otro estado responde 409.",
    responses={**_R401, **_R403, **_R404, **_R409, **_R422},
)
def anular(
    id: uuid.UUID,
    entrada: MotivoEntrada,
    usuario: UsuarioActual = Depends(solo_oficial),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> RequerimientoSalida:
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_anular(uow.sesion).ejecutar(actor, id, entrada.motivo)
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)
