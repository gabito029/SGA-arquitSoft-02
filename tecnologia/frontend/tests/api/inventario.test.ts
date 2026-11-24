// T105: el stock de todas las páginas, por item_id.
import { stockPorItem } from '../../src/api/inventario';
import { ITEM_INT_1, ITEM_INT_2 } from '../apoyo/catalogo';
import { respuesta, simularFetch } from '../apoyo/respuestas';

describe('stockPorItem', () => {
  it('recorre todas las páginas', async () => {
    const fetchSimulado = simularFetch(
      respuesta(200, { items: [{ item: ITEM_INT_1, cantidad: 10 }], total: 51, page: 1, size: 50 }),
      respuesta(200, { items: [{ item: ITEM_INT_2, cantidad: 0 }], total: 51, page: 2, size: 50 }),
    );
    expect(await stockPorItem()).toEqual({ [ITEM_INT_1.id]: 10, [ITEM_INT_2.id]: 0 });
    expect(fetchSimulado.mock.calls.map((c) => c[0])).toEqual([
      '/api/v1/inventario/stock?page=1&size=50',
      '/api/v1/inventario/stock?page=2&size=50',
    ]);
  });

  it('termina con una página vacía', async () => {
    simularFetch(respuesta(200, { items: [], total: 0, page: 1, size: 50 }));
    expect(await stockPorItem()).toEqual({});
  });
});
