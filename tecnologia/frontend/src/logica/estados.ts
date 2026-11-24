// Etiquetas de los estados en la interfaz (tabla "Estados de la solicitud" de spec.md).
import type { EstadoRequerimiento, NivelFirma, Rol } from '../api/tipos';

export const ETIQUETAS_ESTADO: Record<EstadoRequerimiento, string> = {
  BORRADOR: 'Registrada',
  PENDIENTE_VB_UNIDAD: 'En visto bueno de la unidad',
  PENDIENTE_CONFORMIDAD: 'En conformidad de la División/Brigada',
  PENDIENTE_AUTORIZACION_COLOGE: 'En autorización del COLOGE',
  PENDIENTE_APROBACION: 'En aprobación del almacén',
  APROBADA: 'Aprobada',
  EN_TRANSITO: 'Despachada',
  CONFIRMADA: 'Recibida',
  RECHAZADA: 'Rechazada',
  ANULADA: 'Anulada',
};

export type TonoEstado = 'neutral' | 'en-curso' | 'exito' | 'alerta';

const TONOS: Record<EstadoRequerimiento, TonoEstado> = {
  BORRADOR: 'neutral',
  PENDIENTE_VB_UNIDAD: 'en-curso',
  PENDIENTE_CONFORMIDAD: 'en-curso',
  PENDIENTE_AUTORIZACION_COLOGE: 'en-curso',
  PENDIENTE_APROBACION: 'en-curso',
  APROBADA: 'en-curso',
  EN_TRANSITO: 'en-curso',
  CONFIRMADA: 'exito',
  RECHAZADA: 'alerta',
  ANULADA: 'neutral',
};

export const ESTADOS_FINALES: ReadonlySet<EstadoRequerimiento> = new Set([
  'CONFIRMADA',
  'RECHAZADA',
  'ANULADA',
]);

export function etiquetaEstado(estado: EstadoRequerimiento): string {
  return ETIQUETAS_ESTADO[estado] ?? estado;
}

export function tonoEstado(estado: EstadoRequerimiento): TonoEstado {
  return TONOS[estado] ?? 'neutral';
}

export function esEstadoFinal(estado: EstadoRequerimiento): boolean {
  return ESTADOS_FINALES.has(estado);
}

export const ETIQUETAS_NIVEL: Record<NivelFirma, string> = {
  VB_UNIDAD: 'Visto bueno de la unidad',
  CONFORMIDAD_GU: 'Conformidad de la División/Brigada',
  APROBACION_ALMACEN: 'Aprobación del almacén',
  ACTA_RECEPCION: 'Acta de recepción',
};

const ESTADOS_DE_ALMACEN: EstadoRequerimiento[] = [
  'PENDIENTE_APROBACION',
  'APROBADA',
  'EN_TRANSITO',
  'CONFIRMADA',
  'RECHAZADA',
];

/**
 * Estados por los que cada rol puede filtrar su bandeja (data-model.md §7): solo los oficiales
 * ven los borradores y el almacén ve lo que llega a su nivel. No se ofrece el estado del COLOGE,
 * que no se alcanza en este incremento.
 */
export function estadosFiltrables(rol: Rol | undefined): EstadoRequerimiento[] {
  if (rol === 'JEFE_ALMACEN' || rol === 'ALMACENERO') return ESTADOS_DE_ALMACEN;
  const todos = (Object.keys(ETIQUETAS_ESTADO) as EstadoRequerimiento[]).filter(
    (e) => e !== 'PENDIENTE_AUTORIZACION_COLOGE',
  );
  return rol === 'OFICIAL_LOGISTICA' ? todos : todos.filter((e) => e !== 'BORRADOR');
}