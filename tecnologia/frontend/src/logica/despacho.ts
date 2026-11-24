// Validación del despacho antes de enviarlo (FR-018): por ítem, un entero entre 0 y lo
// solicitado, y al menos un ítem con cantidad mayor que 0. El stock lo valida la API (409).
import type { ItemRequerimiento } from '../api/tipos';

export interface LineaDespacho {
  item_id: string;
  cantidad: number;
}

export interface ResultadoDespacho {
  valido: boolean;
  /** Error por `item_id`. */
  errores: Record<string, string>;
  general?: string;
}

/** Cantidades iniciales: lo solicitado de cada ítem, como texto para los campos. */
export function cantidadesIniciales(items: ItemRequerimiento[]): Record<string, string> {
  return Object.fromEntries(items.map((i) => [i.item.id, String(i.cantidad_solicitada)]));
}

export function validarDespacho(
  items: ItemRequerimiento[],
  cantidades: Record<string, string>,
): ResultadoDespacho {
  const errores: Record<string, string> = {};
  let alguna = false;
  for (const i of items) {
    const texto = (cantidades[i.item.id] ?? '').trim();
    const valor = Number(texto);
    if (texto === '' || !Number.isInteger(valor) || valor < 0) {
      errores[i.item.id] = 'Indique un número entero mayor o igual a 0.';
    } else if (valor > i.cantidad_solicitada) {
      errores[i.item.id] = `No puede superar lo solicitado (${i.cantidad_solicitada}).`;
    } else if (valor > 0) {
      alguna = true;
    }
  }
  const valido = Object.keys(errores).length === 0 && alguna;
  return {
    valido,
    errores,
    general:
      Object.keys(errores).length === 0 && !alguna
        ? 'Debe despachar al menos un ítem con cantidad mayor que 0.'
        : undefined,
  };
}

export function cuerpoDespacho(
  items: ItemRequerimiento[],
  cantidades: Record<string, string>,
): { items: LineaDespacho[] } {
  return {
    items: items.map((i) => ({ item_id: i.item.id, cantidad: Number(cantidades[i.item.id]) })),
  };
}
