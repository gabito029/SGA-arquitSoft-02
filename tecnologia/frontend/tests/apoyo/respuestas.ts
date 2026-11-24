// Respuestas simuladas de fetch para las pruebas (jsdom no trae fetch ni Response).
import type { Token, Usuario } from '../../src/api/tipos';

export function respuesta(estado: number, cuerpo?: unknown): Response {
  return {
    ok: estado >= 200 && estado < 300,
    status: estado,
    json: async () => {
      if (cuerpo === undefined) throw new SyntaxError('Sin cuerpo JSON');
      return cuerpo;
    },
  } as unknown as Response;
}

export function simularFetch(...respuestas: (Response | Error)[]): jest.Mock {
  const simulado = jest.fn();
  for (const r of respuestas) {
    if (r instanceof Error) simulado.mockRejectedValueOnce(r);
    else simulado.mockResolvedValueOnce(r);
  }
  globalThis.fetch = simulado as unknown as typeof fetch;
  return simulado;
}

export const USUARIO_OFICIAL: Usuario = {
  id: '11111111-1111-1111-1111-111111111111',
  usuario: 'oficial.bim11',
  nombre_completo: 'Oficial de logística BIM-11',
  rol: 'OFICIAL_LOGISTICA',
  organo: { id: '22222222-2222-2222-2222-222222222222', codigo: 'BIM-11', nombre: 'BIM N.° 11' },
  almacen_id: null,
};

export function token(usuario: Usuario = USUARIO_OFICIAL): Token {
  return { access_token: 'token-de-prueba', token_type: 'bearer', expira_en: 3600, usuario };
}
