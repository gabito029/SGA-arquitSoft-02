// Ítems y requerimientos ficticios para las pruebas del formulario de solicitud.
import type { Item, Requerimiento } from '../../src/api/tipos';

export const ITEM_INT_1: Item = {
  id: 'aaaaaaaa-0000-0000-0000-000000000001',
  codigo: 'INT-001',
  nombre: 'Ración de campaña',
  categoria: 'INTENDENCIA',
  unidad_medida: 'unidad',
  valor_unitario: '35.50',
};

export const ITEM_INT_2: Item = {
  id: 'aaaaaaaa-0000-0000-0000-000000000002',
  codigo: 'INT-002',
  nombre: 'Uniforme de campaña',
  categoria: 'INTENDENCIA',
  unidad_medida: 'unidad',
  valor_unitario: '180.00',
};

export const ITEM_MG_1: Item = {
  id: 'bbbbbbbb-0000-0000-0000-000000000001',
  codigo: 'MG-001',
  nombre: 'Casco balístico',
  categoria: 'MATERIAL_GUERRA',
  unidad_medida: 'unidad',
  valor_unitario: '1200.00',
};

export function requerimiento(parcial: Partial<Requerimiento> = {}): Requerimiento {
  return {
    id: 'cccccccc-0000-0000-0000-000000000001',
    codigo: 'REQ-2026-000001',
    estado: 'BORRADOR',
    categoria: 'INTENDENCIA',
    unidad: { id: 'u1', codigo: 'BIM-11', nombre: 'BIM N.° 11' },
    monto_total: null,
    items: [{ item: ITEM_INT_1, cantidad_solicitada: 2 }],
    creado_en: '2026-11-23T10:00:00Z',
    acciones_disponibles: ['EDITAR', 'ENVIAR', 'ANULAR'],
    ...parcial,
  };
}
