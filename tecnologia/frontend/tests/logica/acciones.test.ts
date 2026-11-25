// T065: solo aparecen las acciones permitidas y el motivo es obligatorio.
import {
  accionesVisibles,
  accionPendiente,
  decisionAprobar,
  decisionRechazar,
  ETIQUETAS_ACCION,
  puede,
  validarMotivo,
} from '../../src/logica/acciones';
import { ETIQUETAS_NIVEL, estadosFiltrables } from '../../src/logica/estados';
import { requerimiento } from '../apoyo/catalogo';

describe('acciones disponibles', () => {
  it('solo permite lo que la API incluye en acciones_disponibles', () => {
    const r = requerimiento({ estado: 'PENDIENTE_VB_UNIDAD', acciones_disponibles: ['FIRMAR', 'RECHAZAR'] });
    expect(puede(r, 'FIRMAR')).toBe(true);
    expect(puede(r, 'RECHAZAR')).toBe(true);
    expect(puede(r, 'DESPACHAR')).toBe(false);
    expect(puede(null, 'FIRMAR')).toBe(false);
  });

  it('ordena las acciones visibles y filtra las que la pantalla no soporta', () => {
    const r = requerimiento({ acciones_disponibles: ['ANULAR', 'ENVIAR', 'EDITAR'] });
    expect(accionesVisibles(r)).toEqual(['ENVIAR', 'EDITAR', 'ANULAR']);
    expect(accionesVisibles(r, ['ANULAR'])).toEqual(['ANULAR']);
    expect(accionesVisibles(requerimiento({ acciones_disponibles: [] }))).toEqual([]);
  });

  it('tiene una etiqueta en español para cada acción', () => {
    expect(ETIQUETAS_ACCION.FIRMAR_ACTA).toBe('Firmar acta');
    expect(ETIQUETAS_NIVEL.CONFORMIDAD_GU).toBe('Conformidad de la División/Brigada');
  });
});

describe('accionPendiente (T101)', () => {
  it.each([
    [['FIRMAR', 'RECHAZAR'], 'Por firmar'],
    [['DESPACHAR'], 'Por despachar'],
    [['FIRMAR_ACTA'], 'Por firmar el acta'],
    [['EDITAR', 'ENVIAR', 'ANULAR'], 'Por enviar'],
    [['ANULAR'], 'Por revisar'],
    [[], null],
  ] as const)('%j → %s', (acciones, esperado) => {
    expect(accionPendiente(acciones)).toBe(esperado);
  });
});

describe('validarMotivo', () => {
  it('exige el motivo', () => {
    expect(validarMotivo('')).toBe('Indique el motivo.');
    expect(validarMotivo('    ')).toBe('Indique el motivo.');
  });

  it('exige entre 5 y 500 caracteres', () => {
    expect(validarMotivo('abc')).toMatch(/al menos 5/);
    expect(validarMotivo('x'.repeat(501))).toMatch(/500/);
    expect(validarMotivo('Cantidad excesiva')).toBeNull();
  });

  it('arma el cuerpo de la decisión sin espacios sobrantes', () => {
    expect(decisionAprobar()).toEqual({ decision: 'APROBAR', documento_revisado: true });
    expect(decisionRechazar('  Sin stock  ')).toEqual({
      decision: 'RECHAZAR',
      motivo: 'Sin stock',
      documento_revisado: true,
    });
  });
});

describe('estadosFiltrables', () => {
  it('solo el oficial filtra borradores y el almacén ve su parte del flujo', () => {
    expect(estadosFiltrables('OFICIAL_LOGISTICA')).toContain('BORRADOR');
    expect(estadosFiltrables('COMANDANTE_UNIDAD')).not.toContain('BORRADOR');
    expect(estadosFiltrables('AUDITOR')).not.toContain('PENDIENTE_AUTORIZACION_COLOGE');
    expect(estadosFiltrables('ALMACENERO')).toEqual([
      'PENDIENTE_APROBACION',
      'APROBADA',
      'EN_TRANSITO',
      'CONFIRMADA',
      'RECHAZADA',
    ]);
  });
});
