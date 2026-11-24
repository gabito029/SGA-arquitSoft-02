// T099: la ruta de retorno solo vale para la misma sesión (mismo usuario, misma pestaña).
import {
  borrarRetorno,
  CLAVE_RETORNO,
  destinoTrasIngreso,
  guardarRetorno,
  RUTA_BANDEJA,
} from '../../src/logica/retorno';

afterEach(() => sessionStorage.clear());

describe('ruta de retorno', () => {
  it('sin ruta guardada va a la bandeja', () => {
    expect(destinoTrasIngreso('u1')).toBe(RUTA_BANDEJA);
  });

  it('el mismo usuario retoma su ruta, una sola vez', () => {
    guardarRetorno('/solicitudes/abc?x=1', 'u1');
    expect(destinoTrasIngreso('u1')).toBe('/solicitudes/abc?x=1');
    expect(destinoTrasIngreso('u1')).toBe(RUTA_BANDEJA);
  });

  it('otro usuario va a la bandeja y la ruta ajena se descarta', () => {
    guardarRetorno('/solicitudes/abc', 'u1');
    expect(destinoTrasIngreso('u2')).toBe(RUTA_BANDEJA);
    expect(sessionStorage.getItem(CLAVE_RETORNO)).toBeNull();
  });

  it('al cerrar sesión se borra', () => {
    guardarRetorno('/stock', 'u1');
    borrarRetorno();
    expect(destinoTrasIngreso('u1')).toBe(RUTA_BANDEJA);
  });

  it.each(['https://otro.sitio/x', '//otro.sitio', '/ingresar', 'relativa'])(
    'no guarda rutas externas ni la de ingreso: %s',
    (ruta) => {
      guardarRetorno(ruta, 'u1');
      expect(sessionStorage.getItem(CLAVE_RETORNO)).toBeNull();
    },
  );

  it('ignora datos dañados', () => {
    sessionStorage.setItem(CLAVE_RETORNO, '{no es json');
    expect(destinoTrasIngreso('u1')).toBe(RUTA_BANDEJA);
    sessionStorage.setItem(CLAVE_RETORNO, JSON.stringify({ ruta: 5 }));
    expect(destinoTrasIngreso('u1')).toBe(RUTA_BANDEJA);
  });
});
