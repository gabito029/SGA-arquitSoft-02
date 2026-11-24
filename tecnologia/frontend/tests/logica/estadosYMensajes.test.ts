// Etiquetas de estado (spec.md) y elección del mensaje de error.
import type { EstadoRequerimiento } from '../../src/api/tipos';
import {
  esEstadoFinal,
  ETIQUETAS_ESTADO,
  etiquetaEstado,
  resumenPorTono,
  tonoEstado,
} from '../../src/logica/estados';
import {
  MENSAJE_GENERICO,
  MENSAJES_POR_CODIGO,
  mensajeDeError,
} from '../../src/logica/mensajes';

describe('estados', () => {
  it('usa las etiquetas de la tabla de estados de spec.md', () => {
    expect(etiquetaEstado('BORRADOR')).toBe('Registrada');
    expect(etiquetaEstado('PENDIENTE_VB_UNIDAD')).toBe('En visto bueno de la unidad');
    expect(etiquetaEstado('PENDIENTE_CONFORMIDAD')).toBe('En conformidad de la División/Brigada');
    expect(etiquetaEstado('PENDIENTE_APROBACION')).toBe('En aprobación del almacén');
    expect(etiquetaEstado('EN_TRANSITO')).toBe('Despachada');
    expect(etiquetaEstado('CONFIRMADA')).toBe('Recibida');
  });

  it('tiene una etiqueta para cada uno de los 10 estados', () => {
    expect(Object.keys(ETIQUETAS_ESTADO)).toHaveLength(10);
  });

  it('identifica los estados finales y su tono', () => {
    const finales: EstadoRequerimiento[] = ['CONFIRMADA', 'RECHAZADA', 'ANULADA'];
    finales.forEach((estado) => expect(esEstadoFinal(estado)).toBe(true));
    expect(esEstadoFinal('APROBADA')).toBe(false);
  });

  it('usa un tono consistente por estado (T108)', () => {
    expect(tonoEstado('BORRADOR')).toBe('neutral');
    expect(tonoEstado('PENDIENTE_VB_UNIDAD')).toBe('pendiente');
    expect(tonoEstado('PENDIENTE_APROBACION')).toBe('pendiente');
    expect(tonoEstado('APROBADA')).toBe('aprobada');
    expect(tonoEstado('EN_TRANSITO')).toBe('transito');
    expect(tonoEstado('CONFIRMADA')).toBe('recibida');
    expect(tonoEstado('RECHAZADA')).toBe('rechazada');
    expect(tonoEstado('ANULADA')).toBe('rechazada');
  });

  it('resume una página de solicitudes por tono, en orden y sin grupos vacíos (T110)', () => {
    const resumen = resumenPorTono([
      { estado: 'RECHAZADA' },
      { estado: 'PENDIENTE_VB_UNIDAD' },
      { estado: 'ANULADA' },
      { estado: 'PENDIENTE_CONFORMIDAD' },
      { estado: 'CONFIRMADA' },
    ]);
    expect(resumen).toEqual([
      { tono: 'pendiente', etiqueta: 'En trámite', cantidad: 2 },
      { tono: 'recibida', etiqueta: 'Recibidas', cantidad: 1 },
      { tono: 'rechazada', etiqueta: 'Rechazadas o anuladas', cantidad: 2 },
    ]);
    expect(resumenPorTono([])).toEqual([]);
  });

  it('devuelve el valor original si llega un estado desconocido', () => {
    const desconocido = 'OTRO' as EstadoRequerimiento;
    expect(etiquetaEstado(desconocido)).toBe('OTRO');
    expect(tonoEstado(desconocido)).toBe('neutral');
  });
});

describe('mensajeDeError', () => {
  it.each(Object.keys(MENSAJES_POR_CODIGO))('tiene un mensaje propio para %s', (codigo) => {
    expect(mensajeDeError(409, codigo, 'texto del servidor')).toBe(MENSAJES_POR_CODIGO[codigo]);
  });

  it('usa el mensaje del servidor cuando el código no tiene uno propio', () => {
    expect(mensajeDeError(422, 'VALIDACION', 'Revise la cantidad.')).toBe('Revise la cantidad.');
  });

  it('usa el genérico para un estado HTTP sin mensaje', () => {
    expect(mensajeDeError(418)).toBe(MENSAJE_GENERICO);
    expect(mensajeDeError(400, undefined, '   ')).toBe(MENSAJE_GENERICO);
  });
});
