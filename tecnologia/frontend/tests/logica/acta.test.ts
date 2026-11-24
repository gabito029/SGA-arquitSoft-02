// Lógica del acta de recepción (FR-021).
import {
  cuerpoActa,
  ETIQUETAS_VERIFICACION,
  hayDiferencia,
  recepcionInicial,
  validarActa,
} from '../../src/logica/acta';
import { ITEM_INT_1, ITEM_INT_2 } from '../apoyo/catalogo';

const ITEMS = [
  { item: ITEM_INT_1, cantidad_solicitada: 10, cantidad_despachada: 10 },
  { item: ITEM_INT_2, cantidad_solicitada: 5, cantidad_despachada: null },
];

describe('acta', () => {
  it('propone lo despachado (0 si no se despachó)', () => {
    expect(recepcionInicial(ITEMS)).toEqual({
      [ITEM_INT_1.id]: { cantidad: '10', observacion: '' },
      [ITEM_INT_2.id]: { cantidad: '0', observacion: '' },
    });
  });

  it('detecta diferencias', () => {
    expect(hayDiferencia(ITEMS[0], { cantidad: '10', observacion: '' })).toBe(false);
    expect(hayDiferencia(ITEMS[0], { cantidad: '9', observacion: '' })).toBe(true);
    expect(hayDiferencia(ITEMS[0], { cantidad: ' ', observacion: '' })).toBe(true);
    expect(hayDiferencia(ITEMS[0], undefined)).toBe(true);
    expect(hayDiferencia(ITEMS[1], { cantidad: '0', observacion: '' })).toBe(false);
  });

  it('valida cantidades y observaciones', () => {
    expect(validarActa(ITEMS, recepcionInicial(ITEMS))).toEqual({});
    const errores = validarActa(ITEMS, {
      [ITEM_INT_1.id]: { cantidad: '-1', observacion: '' },
      [ITEM_INT_2.id]: { cantidad: '1', observacion: 'x'.repeat(501) },
    });
    expect(errores[ITEM_INT_1.id]).toMatch(/entero/);
    expect(errores[ITEM_INT_2.id]).toMatch(/500/);
    expect(validarActa(ITEMS, {})[ITEM_INT_1.id]).toMatch(/entero/);
  });

  it('arma el cuerpo sin observaciones vacías', () => {
    expect(
      cuerpoActa(ITEMS, {
        [ITEM_INT_1.id]: { cantidad: '9', observacion: '  Una dañada ' },
        [ITEM_INT_2.id]: { cantidad: '0', observacion: '   ' },
      }),
    ).toEqual({
      items: [
        { item_id: ITEM_INT_1.id, cantidad_recibida: 9, observacion: 'Una dañada' },
        { item_id: ITEM_INT_2.id, cantidad_recibida: 0 },
      ],
    });
    expect(ETIQUETAS_VERIFICACION.ALTERADA).toBe('Alterada');
  });
});
