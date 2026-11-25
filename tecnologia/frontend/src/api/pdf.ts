// PDF verificable (incremento 002): descargar el PDF del requerimiento o del acta (US3, US4) y
// verificar un PDF subido (US5). Usan el mismo token y los mismos mensajes de error que el resto
// de la API, pero con cuerpos binarios.
import { solicitarBinario } from './cliente';
import type { VerificacionPdf } from './tipos';

/** Tamaño máximo de un PDF a verificar (FR-016): 5 MB, igual que la API. */
export const PDF_TAMANO_MAXIMO = 5 * 1024 * 1024;

export type DestinoPdf = 'requerimiento' | 'acta';

export function rutaPdf(id: string, destino: DestinoPdf): string {
  return destino === 'acta'
    ? `/requerimientos/${id}/acta/documento.pdf`
    : `/requerimientos/${id}/documento.pdf`;
}

/** Descarga el PDF y lo guarda con un enlace temporal (sin abrir ventanas ni diálogos). */
export async function descargarPdf(id: string, destino: DestinoPdf, nombre: string): Promise<void> {
  const respuesta = await solicitarBinario(rutaPdf(id, destino), { aceptar: 'application/pdf' });
  const archivo = await respuesta.blob();
  const url = URL.createObjectURL(archivo);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

/** Problema del archivo elegido antes de enviarlo, o null si se puede verificar. */
export function validarArchivoPdf(archivo: File | null): string | null {
  if (!archivo) return 'Elija un archivo PDF.';
  if (archivo.size === 0) return 'El archivo está vacío.';
  if (archivo.size > PDF_TAMANO_MAXIMO) return 'El archivo supera el tamaño máximo de 5 MB.';
  const esPdf = archivo.type === 'application/pdf' || archivo.name.toLowerCase().endsWith('.pdf');
  return esPdf ? null : 'El archivo no es un PDF.';
}

export async function verificarPdf(archivo: Blob): Promise<VerificacionPdf> {
  const respuesta = await solicitarBinario('/documentos/verificacion', {
    metodo: 'POST',
    cuerpo: archivo,
    tipo: 'application/pdf',
  });
  return (await respuesta.json()) as VerificacionPdf;
}
