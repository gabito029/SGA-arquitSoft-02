// T043: reglas del formulario de nueva solicitud (FR-005, FR-007; escenario 3 de la US1).
import {
  aEntrada,
  CAMPOS_FORMULARIO,
  esValida,
  leerCantidad,
  MAXIMO_CAMPOS_VISIBLES,
  MENSAJES_VALIDACION,
  validarLinea,
  validarSolicitud,
} from '../../src/logica/validacionSolicitud';
import { ITEM_INT_1, ITEM_INT_2, ITEM_MG_1 } from '../apoyo/catalogo';

describe('leerCantidad', () => {
  it.each([
    ['1', 1],
    [' 25 ', 25],
    [7, 7],
  ])('acepta el entero positivo %p', (valor, esperado) => {
    expect(leerCantidad(valor)).toBe(esperado);
  });

  it.each(['0', '-2', '1.5', '2,5', 'abc', '', '1e3', 0, -1, 2.5])('rechaza %p', (valor) => {
    expect(leerCantidad(valor)).toBeNull();
  });
});

describe('validarSolicitud', () => {
  it('exige al menos un ítem', () => {
    expect(validarSolicitud([])).toEqual({ items: MENSAJES_VALIDACION.sinItems });
  });

  it('acepta ítems de una sola categoría con cantidades enteras positivas', () => {
    const errores = validarSolicitud([
      { item: ITEM_INT_1, cantidad: 10 },
      { item: ITEM_INT_2, cantidad: 5 },
    ]);
    expect(esValida(errores)).toBe(true);
  });

  it('rechaza la cantidad cero o no entera, indicando la línea', () => {
    const errores = validarSolicitud([
      { item: ITEM_INT_1, cantidad: 0 },
      { item: ITEM_INT_2, cantidad: 1.5 },
    ]);
    expect(errores['items.0.cantidad']).toBe(MENSAJES_VALIDACION.cantidad);
    expect(errores['items.1.cantidad']).toBe(MENSAJES_VALIDACION.cantidad);
  });

  it('rechaza un ítem repetido', () => {
    const errores = validarSolicitud([
      { item: ITEM_INT_1, cantidad: 1 },
      { item: ITEM_INT_1, cantidad: 2 },
    ]);
    expect(errores['items.1.item_id']).toBe(MENSAJES_VALIDACION.repetido);
    expect(esValida(errores)).toBe(false);
  });

  it('exige una sola categoría', () => {
    const errores = validarSolicitud([
      { item: ITEM_INT_1, cantidad: 1 },
      { item: ITEM_MG_1, cantidad: 1 },
    ]);
    expect(errores.items).toBe(MENSAJES_VALIDACION.categoria);
  });
});

describe('validarLinea', () => {
  it('pide elegir un ítem y una cantidad válida', () => {
    expect(validarLinea(undefined, '0', [], 'INTENDENCIA')).toEqual({
      item: MENSAJES_VALIDACION.sinItem,
      cantidad: MENSAJES_VALIDACION.cantidad,
    });
  });

  it('no deja agregar un ítem que ya está en la lista', () => {
    const lineas = [{ item: ITEM_INT_1, cantidad: 1 }];
    expect(validarLinea(ITEM_INT_1, '3', lineas, 'INTENDENCIA').item).toBe(
      MENSAJES_VALIDACION.repetido,
    );
  });

  it('no deja agregar un ítem de otra categoría', () => {
    expect(validarLinea(ITEM_MG_1, '3', [], 'INTENDENCIA').item).toBe(
      MENSAJES_VALIDACION.categoria,
    );
  });

  it('acepta un ítem nuevo de la categoría con cantidad válida', () => {
    expect(validarLinea(ITEM_INT_2, '4', [{ item: ITEM_INT_1, cantidad: 1 }], 'INTENDENCIA')).toEqual(
      {},
    );
  });
});

describe('formulario', () => {
  it('muestra 5 campos como máximo (FR-005)', () => {
    expect(CAMPOS_FORMULARIO.length).toBeLessThanOrEqual(MAXIMO_CAMPOS_VISIBLES);
    expect(MAXIMO_CAMPOS_VISIBLES).toBe(5);
  });

  it('arma el cuerpo de la API con item_id y cantidad', () => {
    expect(aEntrada([{ item: ITEM_INT_1, cantidad: 3 }])).toEqual({
      items: [{ item_id: ITEM_INT_1.id, cantidad: 3 }],
    });
  });
});
