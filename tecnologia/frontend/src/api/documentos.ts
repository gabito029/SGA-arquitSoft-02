// Documento oficial y PDF verificable (incremento 002): ver el documento, descargar el PDF
// del requerimiento o del acta y verificar un PDF subido.
import { api } from './cliente';
import type { Documento } from './tipos';

export function obtenerDocumento(id: string): Promise<Documento> {
  return api.get<Documento>(`/requerimientos/${id}/documento`);
}

export function obtenerDocumentoActa(id: string): Promise<Documento> {
  return api.get<Documento>(`/requerimientos/${id}/acta/documento`);
}
