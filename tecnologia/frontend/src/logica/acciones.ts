// Acciones sobre una solicitud: la interfaz solo muestra las que la API incluye en
// `acciones_disponibles` (FR-029) y valida el motivo antes de enviarlo.
import type { AccionDisponible, DecisionFirma, Requerimiento } from '../api/tipos';

export const ETIQUETAS_ACCION: Record<AccionDisponible, string> = {
  EDITAR: 'Editar',
  ENVIAR: 'Enviar',
  ANULAR: 'Anular',
  FIRMAR: 'Firmar',
  RECHAZAR: 'Rechazar',
  DESPACHAR: 'Despachar',
  FIRMAR_ACTA: 'Firmar acta',
};

/** Orden en el que se muestran los botones. */
const ORDEN: AccionDisponible[] = [
  'FIRMAR',
  'RECHAZAR',
  'DESPACHAR',
  'FIRMAR_ACTA',
  'ENVIAR',
  'EDITAR',
  'ANULAR',
];

export const MOTIVO_MINIMO = 5;
export const MOTIVO_MAXIMO = 500;

export function puede(req: Requerimiento | null | undefined, accion: AccionDisponible): boolean {
  return Boolean(req?.acciones_disponibles.includes(accion));
}

/**
 * Acciones que se muestran para `req`: las que permite la API y, de ellas, solo las que esta
 * pantalla sabe ejecutar (`soportadas`).
 */
export function accionesVisibles(
  req: Requerimiento,
  soportadas: readonly AccionDisponible[] = ORDEN,
): AccionDisponible[] {
  return ORDEN.filter((a) => soportadas.includes(a) && req.acciones_disponibles.includes(a));
}

/** Devuelve el error del motivo, o null si es válido (obligatorio, 5 a 500 caracteres). */
export function validarMotivo(motivo: string): string | null {
  const limpio = motivo.trim();
  if (limpio === '') return 'Indique el motivo.';
  if (limpio.length < MOTIVO_MINIMO) {
    return `El motivo debe tener al menos ${MOTIVO_MINIMO} caracteres.`;
  }
  if (limpio.length > MOTIVO_MAXIMO) {
    return `El motivo no puede superar los ${MOTIVO_MAXIMO} caracteres.`;
  }
  return null;
}

export function decisionAprobar(): DecisionFirma {
  return { decision: 'APROBAR' };
}

export function decisionRechazar(motivo: string): DecisionFirma {
  return { decision: 'RECHAZAR', motivo: motivo.trim() };
}

// --- Paso de confirmación (T100): lo que no se puede deshacer ---
export const ADVERTENCIA_FIRMA =
  'La firma digital queda registrada con su nombre, su órgano y la fecha, y no se puede deshacer.';
export const ADVERTENCIA_RECHAZO =
  'El rechazo se firma digitalmente y no se puede deshacer: la solicitud queda Rechazada y nadie ' +
  'más podrá actuar sobre ella.';
export const ADVERTENCIA_DESPACHO =
  'El despacho descuenta el stock en este momento y no se puede deshacer.';
export const ADVERTENCIA_ACTA =
  'El acta se firma digitalmente y no se puede deshacer: lo recibido y las diferencias quedan ' +
  'registrados tal como los indicó.';

// --- Texto de la acción pendiente en la bandeja (T101) ---

/** "Por enviar", "Por firmar"…: lo que el usuario actual tiene que hacer con la solicitud. */
export function accionPendiente(acciones: readonly AccionDisponible[]): string | null {
  if (acciones.includes('FIRMAR') || acciones.includes('RECHAZAR')) return 'Por firmar';
  if (acciones.includes('DESPACHAR')) return 'Por despachar';
  if (acciones.includes('FIRMAR_ACTA')) return 'Por firmar el acta';
  if (acciones.includes('ENVIAR') || acciones.includes('EDITAR')) return 'Por enviar';
  if (acciones.includes('ANULAR')) return 'Por revisar';
  return null;
}
