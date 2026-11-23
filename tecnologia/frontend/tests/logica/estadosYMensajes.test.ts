// Etiquetas de estado (spec.md) y elección del mensaje de error.
import type { EstadoRequerimiento } from '../../src/api/tipos';
import { esEstadoFinal, ETIQUETAS_ESTADO, etiquetaEstado, tonoEstado } from '../../src/logica/estados';
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
    expect(tonoEstado('CONFIRMADA')).toBe('exito');
    expect(tonoEstado('RECHAZADA')).toBe('alerta');
    expect(tonoEstado('PENDIENTE_VB_UNIDAD')).toBe('en-curso');
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
