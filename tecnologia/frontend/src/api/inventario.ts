// Stock del almacén del usuario (GET /api/v1/inventario/stock, paginado de a 50 como máximo).
import { api } from './cliente';
import type { Stock } from './tipos';

interface PaginaStock {
  items: Stock[];
  total: number;
  page: number;
  size: number;
}

export const TAMANO_PAGINA_STOCK = 50;

/** Recorre todas las páginas y devuelve la cantidad disponible por item_id (T105). */
export async function stockPorItem(): Promise<Record<string, number>> {
  const disponible: Record<string, number> = {};
  for (let pagina = 1; ; pagina += 1) {
    const respuesta = await api.get<PaginaStock>('/inventario/stock', {
      page: pagina,
      size: TAMANO_PAGINA_STOCK,
    });
    for (const fila of respuesta.items) disponible[fila.item.id] = fila.cantidad;
    if (respuesta.items.length === 0 || pagina * respuesta.size >= respuesta.total) {
      return disponible;
    }
  }
}
