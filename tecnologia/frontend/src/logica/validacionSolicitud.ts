// Validación del formulario de nueva solicitud (FR-005, FR-007; escenario 3 de la US1).
// El backend vuelve a validar todo; esto solo da respuesta inmediata al usuario.
import type { Categoria, Item, RequerimientoEntrada } from '../api/tipos';

/** Campos editables del formulario: FR-005 exige 5 como máximo por pantalla. */
export const CAMPOS_FORMULARIO = ['categoria', 'item', 'cantidad'] as const;
export const MAXIMO_CAMPOS_VISIBLES = 5;

export interface LineaSolicitud {
  item: Item;
  cantidad: number;
}

/** Errores por campo, con las mismas claves que usa la API (`items`, `items.0.cantidad`, …). */
export type ErroresSolicitud = Record<string, string>;

export const MENSAJES_VALIDACION = {
  sinItems: 'Agregue al menos un ítem.',
  sinItem: 'Elija un ítem del catálogo.',
  cantidad: 'La cantidad debe ser un número entero mayor que 0.',
  repetido: 'Este ítem ya está en la solicitud.',
  categoria: 'Todos los ítems deben ser de la misma categoría.',
} as const;

/** Convierte lo escrito en el campo cantidad; devuelve null si no es un entero mayor que 0. */
export function leerCantidad(valor: string | number): number | null {
  const texto = String(valor).trim();
  if (!/^\d+$/.test(texto)) return null;
  const numero = Number(texto);
  return Number.isSafeInteger(numero) && numero > 0 ? numero : null;
}

/** Valida un ítem antes de agregarlo a la lista. Devuelve los errores de `item` y `cantidad`. */
export function validarLinea(
  item: Item | undefined,
  cantidad: string | number,
  lineas: readonly LineaSolicitud[],
  categoria: Categoria,
): ErroresSolicitud {
  const errores: ErroresSolicitud = {};
  if (!item) {
    errores.item = MENSAJES_VALIDACION.sinItem;
  } else if (lineas.some((l) => l.item.id === item.id)) {
    errores.item = MENSAJES_VALIDACION.repetido;
  } else if (item.categoria !== categoria) {
    errores.item = MENSAJES_VALIDACION.categoria;
  }
  if (leerCantidad(cantidad) === null) {
    errores.cantidad = MENSAJES_VALIDACION.cantidad;
  }
  return errores;
}

/** Valida la solicitud completa antes de guardarla o enviarla. */
export function validarSolicitud(lineas: readonly LineaSolicitud[]): ErroresSolicitud {
  const errores: ErroresSolicitud = {};
  if (lineas.length === 0) {
    errores.items = MENSAJES_VALIDACION.sinItems;
    return errores;
  }
  const vistos = new Set<string>();
  lineas.forEach((linea, indice) => {
    if (vistos.has(linea.item.id)) {
      errores[`items.${indice}.item_id`] = MENSAJES_VALIDACION.repetido;
    }
    vistos.add(linea.item.id);
    if (leerCantidad(linea.cantidad) === null) {
      errores[`items.${indice}.cantidad`] = MENSAJES_VALIDACION.cantidad;
    }
  });
  if (new Set(lineas.map((l) => l.item.categoria)).size > 1) {
    errores.items = MENSAJES_VALIDACION.categoria;
  }
  return errores;
}

export function esValida(errores: ErroresSolicitud): boolean {
  return Object.keys(errores).length === 0;
}

/** Cuerpo de `POST/PUT /api/v1/requerimientos` (esquema `RequerimientoEntrada`). */
export function aEntrada(lineas: readonly LineaSolicitud[]): RequerimientoEntrada {
  return { items: lineas.map((l) => ({ item_id: l.item.id, cantidad: l.cantidad })) };
}
