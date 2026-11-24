// Validación del despacho (FR-018).
import { cantidadesIniciales, cuerpoDespacho, validarDespacho } from '../../src/logica/despacho';
import { ITEM_INT_1, ITEM_INT_2 } from '../apoyo/catalogo';

const ITEMS = [
  { item: ITEM_INT_1, cantidad_solicitada: 7 },
  { item: ITEM_INT_2, cantidad_solicitada: 3 },
];

describe('validarDespacho', () => {
  it('propone lo solicitado', () => {
    expect(cantidadesIniciales(ITEMS)).toEqual({ [ITEM_INT_1.id]: '7', [ITEM_INT_2.id]: '3' });
    expect(validarDespacho(ITEMS, cantidadesIniciales(ITEMS)).valido).toBe(true);
  });

  it('acepta un despacho parcial con algún ítem en 0', () => {
    expect(validarDespacho(ITEMS, { [ITEM_INT_1.id]: '2', [ITEM_INT_2.id]: '0' }).valido).toBe(true);
  });

  it('rechaza cantidades fuera de rango, decimales o vacías', () => {
    const r = validarDespacho(ITEMS, { [ITEM_INT_1.id]: '8', [ITEM_INT_2.id]: '1.5' });
    expect(r.valido).toBe(false);
    expect(r.errores[ITEM_INT_1.id]).toMatch(/No puede superar/);
    expect(r.errores[ITEM_INT_2.id]).toMatch(/entero/);
    expect(validarDespacho(ITEMS, { [ITEM_INT_1.id]: '', [ITEM_INT_2.id]: '-1' }).valido).toBe(false);
  });

  it('exige al menos un ítem mayor que 0', () => {
    const r = validarDespacho(ITEMS, { [ITEM_INT_1.id]: '0', [ITEM_INT_2.id]: '0' });
    expect(r.valido).toBe(false);
    expect(r.general).toMatch(/al menos un ítem/);
  });

  it('arma el cuerpo con números', () => {
    expect(cuerpoDespacho(ITEMS, { [ITEM_INT_1.id]: '5', [ITEM_INT_2.id]: '0' })).toEqual({
      items: [
        { item_id: ITEM_INT_1.id, cantidad: 5 },
        { item_id: ITEM_INT_2.id, cantidad: 0 },
      ],
    });
  });
});
