// Documento oficial de prueba (incremento 002).
import type { Documento, Sello } from '../../src/api/tipos';

export const SELLO_VB: Sello = {
  firma_id: 'f1',
  nivel: 'VB_UNIDAD',
  decision: 'APROBAR',
  firmante: 'Comandante BIM-11',
  rol: 'COMANDANTE_UNIDAD',
  organo: { codigo: 'BIM-11', nombre: 'BIM N.° 11' },
  firmado_en: '2026-11-24T10:00:00Z',
  metodo: 'ed25519-sha256-v1',
  huella_sha256: `12345678${'0'.repeat(48)}abcdef90`,
};

export function documento(cambios: Partial<Documento> = {}): Documento {
  return {
    tipo: 'REQUERIMIENTO',
    requerimiento_id: 'cccccccc-0000-0000-0000-000000000001',
    codigo: 'REQ-2026-000001',
    unidad: { codigo: 'BIM-11', nombre: 'BIM N.° 11' },
    gran_unidad: { codigo: '1DE', nombre: '1.ª División de Ejército' },
    almacen: { codigo: 'SINTE', nombre: 'Almacén de intendencia' },
    fecha: '2026-11-24T09:00:00Z',
    items: [
      {
        codigo: 'INT-001',
        descripcion: 'Ración de campaña',
        unidad_medida: 'UND',
        categoria: 'INTENDENCIA',
        cantidad_solicitada: 10,
      },
    ],
    sellos: [SELLO_VB],
    huella_contenido: 'f'.repeat(64),
    pdf_disponible: true,
    ...cambios,
  };
}
