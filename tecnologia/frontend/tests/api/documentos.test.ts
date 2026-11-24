// Cliente de documentos (incremento 002).
import { obtenerDocumento, obtenerDocumentoActa } from '../../src/api/documentos';
import { documento } from '../apoyo/documento';
import { respuesta, simularFetch } from '../apoyo/respuestas';

describe('api/documentos', () => {
  it('obtiene el documento del requerimiento y el del acta', async () => {
    const fetchSimulado = simularFetch(respuesta(200, documento()), respuesta(200, documento()));
    await obtenerDocumento('r1');
    await obtenerDocumentoActa('r1');
    expect(fetchSimulado.mock.calls[0][0]).toMatch(/\/requerimientos\/r1\/documento$/);
    expect(fetchSimulado.mock.calls[1][0]).toMatch(/\/requerimientos\/r1\/acta\/documento$/);
  });
});
