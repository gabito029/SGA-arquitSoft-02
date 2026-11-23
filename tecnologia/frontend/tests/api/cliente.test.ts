// T040: cliente de la API.
import { api, ErrorApi, EVENTO_SESION_EXPIRADA, fijarToken, solicitar } from '../../src/api/cliente';
import { MENSAJES_POR_CODIGO, MENSAJES_POR_ESTADO_HTTP } from '../../src/logica/mensajes';
import { respuesta, simularFetch } from '../apoyo/respuestas';

async function capturarError(promesa: Promise<unknown>): Promise<ErrorApi> {
  try {
    await promesa;
  } catch (error) {
    if (error instanceof ErrorApi) return error;
    throw error;
  }
  throw new Error('Se esperaba un ErrorApi');
}

afterEach(() => {
  fijarToken(null);
});

describe('cliente de la API', () => {
  it('agrega el token en la cabecera Authorization', async () => {
    const fetchSimulado = simularFetch(respuesta(200, { ok: true }));
    fijarToken('abc123');
    await api.get('/auth/me');
    const [url, opciones] = fetchSimulado.mock.calls[0];
    expect(url).toBe('/api/v1/auth/me');
    expect(opciones.headers.Authorization).toBe('Bearer abc123');
    expect(opciones.method).toBe('GET');
  });

  it('no envía Authorization sin sesión', async () => {
    const fetchSimulado = simularFetch(respuesta(200, []));
    await api.get('/catalogo/items');
    expect(fetchSimulado.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  it('envía el cuerpo como JSON y arma los parámetros de consulta', async () => {
    const fetchSimulado = simularFetch(respuesta(201, { id: '1' }), respuesta(200, []));
    const creado = await api.post<{ id: string }>('/requerimientos', { categoria: 'INTENDENCIA' });
    expect(creado.id).toBe('1');
    const [, opciones] = fetchSimulado.mock.calls[0];
    expect(opciones.method).toBe('POST');
    expect(opciones.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(opciones.body)).toEqual({ categoria: 'INTENDENCIA' });

    await api.get('/requerimientos', { estado: 'BORRADOR', page: 2, size: undefined });
    expect(fetchSimulado.mock.calls[1][0]).toBe('/api/v1/requerimientos?estado=BORRADOR&page=2');
  });

  it('usa PUT y acepta respuestas sin contenido (204)', async () => {
    const fetchSimulado = simularFetch(respuesta(204));
    await expect(api.put('/requerimientos/1', { items: [] })).resolves.toBeUndefined();
    expect(fetchSimulado.mock.calls[0][1].method).toBe('PUT');
  });

  it('un 401 con sesión dispara el cierre de sesión', async () => {
    simularFetch(respuesta(401, { codigo: 'NO_AUTENTICADO', mensaje: 'La sesión expiró.' }));
    const escucha = jest.fn();
    window.addEventListener(EVENTO_SESION_EXPIRADA, escucha);
    fijarToken('vencido');
    const error = await capturarError(api.get('/auth/me'));
    window.removeEventListener(EVENTO_SESION_EXPIRADA, escucha);
    expect(escucha).toHaveBeenCalledTimes(1);
    expect(error.estado).toBe(401);
    expect(error.message).toBe('La sesión expiró.');
  });

  it('un 401 sin sesión (credenciales incorrectas) no dispara el cierre de sesión', async () => {
    simularFetch(
      respuesta(401, { codigo: 'NO_AUTENTICADO', mensaje: 'Usuario o contraseña incorrectos.' }),
    );
    const escucha = jest.fn();
    window.addEventListener(EVENTO_SESION_EXPIRADA, escucha);
    const error = await capturarError(api.post('/auth/login', { usuario: 'x', contrasena: 'y' }));
    window.removeEventListener(EVENTO_SESION_EXPIRADA, escucha);
    expect(escucha).not.toHaveBeenCalled();
    expect(error.message).toBe('Usuario o contraseña incorrectos.');
  });

  it.each([403, 404, 409, 422])('un %i sin mensaje usa el mensaje en español del código HTTP', async (estado) => {
    simularFetch(respuesta(estado));
    const error = await capturarError(api.get('/requerimientos/1'));
    expect(error.estado).toBe(estado);
    expect(error.codigo).toBe(`HTTP_${estado}`);
    expect(error.message).toBe(MENSAJES_POR_ESTADO_HTTP[estado]);
  });

  it('un 409 con código de negocio usa su mensaje propio', async () => {
    simularFetch(
      respuesta(409, { codigo: 'STOCK_INSUFICIENTE', mensaje: 'Stock insuficiente', detalles: [] }),
    );
    const error = await capturarError(api.post('/requerimientos/1/despacho', { items: [] }));
    expect(error.codigo).toBe('STOCK_INSUFICIENTE');
    expect(error.message).toBe(MENSAJES_POR_CODIGO.STOCK_INSUFICIENTE);
  });

  it('un 422 conserva los detalles por campo', async () => {
    simularFetch(
      respuesta(422, {
        codigo: 'VALIDACION',
        mensaje: 'Los datos enviados no son válidos.',
        detalles: [{ campo: 'items.0.cantidad', mensaje: 'Debe ser mayor que 0.' }],
      }),
    );
    const error = await capturarError(api.post('/requerimientos', {}));
    expect(error.message).toBe('Los datos enviados no son válidos.');
    expect(error.mensajeDeCampo('items.0.cantidad')).toBe('Debe ser mayor que 0.');
    expect(error.mensajeDeCampo('otro')).toBeUndefined();
  });

  it('un error de red muestra un mensaje genérico', async () => {
    simularFetch(new TypeError('Failed to fetch'));
    const error = await capturarError(solicitar('/health'));
    expect(error.estado).toBe(0);
    expect(error.codigo).toBe('ERROR_RED');
    expect(error.message).toBe(MENSAJES_POR_ESTADO_HTTP[0]);
  });

  it('un error 500 sin cuerpo JSON se convierte en un mensaje comprensible', async () => {
    simularFetch(respuesta(500));
    const error = await capturarError(api.get('/requerimientos'));
    expect(error.message).toBe(MENSAJES_POR_ESTADO_HTTP[500]);
  });
});
