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

/**
 * Tono visual de cada estado (T108): pendiente en ámbar, aprobada en verde, despachada en oliva,
 * recibida en azul acero y rechazada o anulada en rojo apagado. Solo cambia el color; los nombres
 * de los estados son los que envía el backend.
 */
export type TonoEstado = 'neutral' | 'pendiente' | 'aprobada' | 'transito' | 'recibida' | 'rechazada';

const TONOS: Record<EstadoRequerimiento, TonoEstado> = {
  BORRADOR: 'neutral',
  PENDIENTE_VB_UNIDAD: 'pendiente',
  PENDIENTE_CONFORMIDAD: 'pendiente',
  PENDIENTE_AUTORIZACION_COLOGE: 'pendiente',
  PENDIENTE_APROBACION: 'pendiente',
  APROBADA: 'aprobada',
  EN_TRANSITO: 'transito',
  CONFIRMADA: 'recibida',
  RECHAZADA: 'rechazada',
  ANULADA: 'rechazada',
};

/** Orden y nombre de cada grupo del resumen de la bandeja (T110). */
export const GRUPOS_RESUMEN: { tono: TonoEstado; etiqueta: string }[] = [
  { tono: 'neutral', etiqueta: 'Registradas' },
  { tono: 'pendiente', etiqueta: 'En trámite' },
  { tono: 'aprobada', etiqueta: 'Aprobadas' },
  { tono: 'transito', etiqueta: 'Despachadas' },
  { tono: 'recibida', etiqueta: 'Recibidas' },
  { tono: 'rechazada', etiqueta: 'Rechazadas o anuladas' },
];

/** Cuántas solicitudes hay de cada tono; solo devuelve los grupos con al menos una. */
export function resumenPorTono(
  solicitudes: { estado: EstadoRequerimiento }[],
): { tono: TonoEstado; etiqueta: string; cantidad: number }[] {
  const conteo = new Map<TonoEstado, number>();
  for (const s of solicitudes) {
    const tono = tonoEstado(s.estado);
    conteo.set(tono, (conteo.get(tono) ?? 0) + 1);
  }
  return GRUPOS_RESUMEN.filter((g) => conteo.has(g.tono)).map((g) => ({
    ...g,
    cantidad: conteo.get(g.tono) as number,
  }));
}

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