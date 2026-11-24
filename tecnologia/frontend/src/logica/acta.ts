// Acta de recepción (FR-021): lo recibido por ítem, sus diferencias con lo despachado y la
// validación antes de firmar. También las etiquetas del resultado de la verificación (FR-024).
import type { ItemRequerimiento, ResultadoVerificacion } from '../api/tipos';

export const OBSERVACION_MAXIMA = 500;

export interface Recibido {
  cantidad: string;
  observacion: string;
}

/** Valor inicial: lo despachado de cada ítem, sin observación. */
export function recepcionInicial(items: ItemRequerimiento[]): Record<string, Recibido> {
  return Object.fromEntries(
    items.map((i) => [i.item.id, { cantidad: String(i.cantidad_despachada ?? 0), observacion: '' }]),
  );
}

/** Verdadero si lo recibido difiere de lo despachado (o aún no es un número válido). */
export function hayDiferencia(item: ItemRequerimiento, recibido: Recibido | undefined): boolean {
  if (!recibido || recibido.cantidad.trim() === '') return true;
  return Number(recibido.cantidad) !== (item.cantidad_despachada ?? 0);
}

export function validarActa(
  items: ItemRequerimiento[],
  recepcion: Record<string, Recibido>,
): Record<string, string> {
  const errores: Record<string, string> = {};
  for (const i of items) {
    const r = recepcion[i.item.id];
    const texto = (r?.cantidad ?? '').trim();
    const valor = Number(texto);
    if (texto === '' || !Number.isInteger(valor) || valor < 0) {
      errores[i.item.id] = 'Indique un número entero mayor o igual a 0.';
    } else if ((r?.observacion ?? '').length > OBSERVACION_MAXIMA) {
      errores[i.item.id] = `La observación no puede superar los ${OBSERVACION_MAXIMA} caracteres.`;
    }
  }
  return errores;
}

export function cuerpoActa(
  items: ItemRequerimiento[],
  recepcion: Record<string, Recibido>,
): { items: { item_id: string; cantidad_recibida: number; observacion?: string }[] } {
  return {
    items: items.map((i) => {
      const r = recepcion[i.item.id];
      const observacion = r.observacion.trim();
      return {
        item_id: i.item.id,
        cantidad_recibida: Number(r.cantidad),
        ...(observacion ? { observacion } : {}),
      };
    }),
  };
}

export const ETIQUETAS_VERIFICACION: Record<ResultadoVerificacion, string> = {
  INTEGRA: 'Íntegra',
  ALTERADA: 'Alterada',
};
