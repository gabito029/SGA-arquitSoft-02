// T104: montos en soles (es-PE) y unidades en plural.
import { cantidadConUnidad, fechaCorta, formatoSoles, unidadMedida } from '../../src/logica/formato';

const normal = (texto: string) => texto.replace(/\u00a0/g, ' ');

describe('formatoSoles', () => {
  it('usa espacio para los miles y coma decimal', () => {
    expect(normal(formatoSoles('1255.00'))).toBe('S/ 1 255,00');
    expect(normal(formatoSoles('35.5'))).toBe('S/ 35,50');
    expect(normal(formatoSoles(1234567.891))).toBe('S/ 1 234 567,89');
    expect(normal(formatoSoles('0'))).toBe('S/ 0,00');
    expect(normal(formatoSoles(-50))).toBe('-S/ 50,00');
  });

  it('no parte el monto en dos líneas (espacios no separables)', () => {
    expect(formatoSoles('1255')).toBe('S/\u00a01\u00a0255,00');
  });

  it('deja tal cual un valor que no es número', () => {
    expect(normal(formatoSoles('abc'))).toBe('S/ abc');
  });
});

describe('unidadMedida', () => {
  it.each([
    ['unidad', 2, 'unidades'],
    ['unidad', 1, 'unidad'],
    ['unidad', 0, 'unidades'],
    ['par', 3, 'pares'],
    ['bidón', 2, 'bidones'],
    ['saco', 4, 'sacos'],
    ['juego', 2, 'juegos'],
    ['luz', 2, 'luces'],
    ['saco de 50 kg', 2, 'sacos de 50 kg'],
    ['', 5, ''],
  ])('%s × %i → %s', (unidad, cantidad, esperado) => {
    expect(unidadMedida(unidad as string, cantidad as number)).toBe(esperado);
  });

  it('arma la cantidad con su unidad', () => {
    expect(cantidadConUnidad(1, 'par')).toBe('1 par');
    expect(cantidadConUnidad(10, 'bidón')).toBe('10 bidones');
  });
});

describe('fechaCorta', () => {
  it('formatea día/mes/año y tolera fechas inválidas', () => {
    expect(fechaCorta('2026-03-05T10:00:00')).toBe('05/03/2026');
    expect(fechaCorta('no-es-fecha')).toBe('');
  });
});
