"""Verificación de un PDF subido (incremento 002, US5; FR-016 a FR-019; EQ-02).

``POST /api/v1/documentos/verificacion`` recibe el archivo como cuerpo ``application/pdf`` (sin
multipart) y responde AUTENTICO o ALTERADO con el motivo. Lo ajeno responde 404, como en 001.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool

from app.core.seguridad import UsuarioActual, usuario_actual
from app.core.unidad_trabajo import FabricaUnidadTrabajo, obtener_fabrica_uow
from app.modules.requests.infraestructura.dependencias import construir_verificar_pdf_subido
from app.modules.requests.presentacion.esquemas import VerificacionPdfSalida
from app.modules.requests.presentacion.router import _R401, _R404, _actor

router = APIRouter(prefix="/api/v1/documentos", tags=["Documentos"])


@router.post(
    "/verificacion",
    response_model=VerificacionPdfSalida,
    summary="Verificar un PDF subido: AUTENTICO o ALTERADO (FR-016 a FR-019, EQ-02)",
    description="AUTENTICO solo si el archivo tiene un código emitido por el SGA, sus bytes "
    "coinciden con la huella SHA-256 firmada con Ed25519 y las firmas que contiene siguen "
    "íntegras con los datos actuales. Cualquier alteración da ALTERADO con el motivo.",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
    responses={
        **_R401,
        **_R404,
        422: {"description": "Vacío, no es un PDF o supera el tamaño máximo (5 MB)"},
    },
)
async def verificar_pdf(
    request: Request,
    usuario: UsuarioActual = Depends(usuario_actual),
    fabrica_uow: FabricaUnidadTrabajo = Depends(obtener_fabrica_uow),
) -> VerificacionPdfSalida:
    contenido = await request.body()

    def verificar():  # la base de datos es síncrona: fuera del bucle de eventos
        with fabrica_uow() as uow:
            vista = construir_verificar_pdf_subido(uow.sesion).ejecutar(_actor(usuario), contenido)
            return VerificacionPdfSalida.desde_vista(vista)

    return await run_in_threadpool(verificar)
