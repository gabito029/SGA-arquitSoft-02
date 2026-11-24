// T106: los colores declarados en estilos.css cumplen WCAG AA (texto ≥ 4,5:1; bordes ≥ 3:1).
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const css = readFileSync(join(__dirname, '../../src/estilos.css'), 'utf-8');

function variable(nombre: string): string {
  const encontrado = css.match(new RegExp(`--${nombre}:\\s*(#[0-9a-fA-F]{6})`));
  if (!encontrado) throw new Error(`No está la variable --${nombre}`);
  return encontrado[1];
}

function luminancia(hex: string): number {
  const canales = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const [r, g, b] = canales.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contraste(a: string, b: string): number {
  const [claro, oscuro] = [luminancia(a), luminancia(b)].sort((x, y) => y - x);
  return (claro + 0.05) / (oscuro + 0.05);
}

describe('contraste (WCAG AA)', () => {
  it('el botón deshabilitado tiene texto legible (≥ 4,5:1)', () => {
    expect(
      contraste(variable('color-deshabilitado-texto'), variable('color-deshabilitado-fondo')),
    ).toBeGreaterThanOrEqual(4.5);
  });

  it('el borde del botón deshabilitado y de los campos se distingue (≥ 3:1)', () => {
    expect(
      contraste(variable('color-deshabilitado-borde'), variable('color-fondo')),
    ).toBeGreaterThanOrEqual(3);
    expect(contraste(variable('color-borde-campo'), '#ffffff')).toBeGreaterThanOrEqual(3);
  });

  it('el botón deshabilitado ya no usa opacidad (bajaba el contraste a 2,97:1)', () => {
    const inicio = css.indexOf('button:disabled');
    const regla = css.slice(inicio, css.indexOf('}', inicio));
    expect(regla).not.toMatch(/opacity/);
    expect(regla).toMatch(/var\(--color-deshabilitado-texto\)/);
  });

  it('los textos principales cumplen 4,5:1', () => {
    const pares: [string, string][] = [
      ['color-texto', 'color-fondo'],
      ['color-texto-suave', 'color-fondo'],
      ['color-aviso', 'color-aviso-fondo'],
      ['color-error', 'color-error-fondo'],
      ['color-exito', 'color-exito-fondo'],
      ['color-texto', 'color-superficie'],
      ['color-texto', 'color-arena'],
      ['color-texto-suave', 'color-superficie'],
      ['color-texto-suave', 'color-arena-suave'],
      ['color-primario', 'color-superficie'],
      ['color-primario', 'color-fondo'],
      ['color-primario', 'color-primario-suave'],
      ['color-acento-texto', 'color-superficie'],
      ['color-acento-texto', 'color-fondo'],
      ['color-sobre-primario', 'color-primario'],
      ['color-sobre-primario', 'color-primario-oscuro'],
      ['color-sobre-primario-suave', 'color-primario'],
      ['color-sobre-primario-suave', 'color-primario-oscuro'],
      ['color-error', 'color-superficie'],
      ['color-aviso', 'color-fondo'],
    ];
    for (const [texto, fondo] of pares) {
      expect(contraste(variable(texto), variable(fondo))).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe('colores de estado (T107, T108)', () => {
  const TONOS = ['neutral', 'pendiente', 'aprobada', 'transito', 'recibida', 'rechazada'];

  it.each(TONOS)('la insignia %s tiene texto legible sobre su fondo (≥ 4,5:1)', (tono) => {
    expect(
      contraste(variable(`estado-${tono}-texto`), variable(`estado-${tono}-fondo`)),
    ).toBeGreaterThanOrEqual(4.5);
  });

  it.each(TONOS)('el color %s se lee sobre la superficie blanca (resumen y sellos)', (tono) => {
    expect(contraste(variable(`estado-${tono}-texto`), variable('color-superficie'))).toBeGreaterThanOrEqual(
      4.5,
    );
  });

  it('el foco se distingue sobre el fondo claro y sobre la cabecera oliva (≥ 3:1)', () => {
    expect(contraste(variable('color-foco'), variable('color-fondo'))).toBeGreaterThanOrEqual(3);
    expect(
      contraste(variable('color-foco-sobre-oscuro'), variable('color-primario')),
    ).toBeGreaterThanOrEqual(3);
  });
});
