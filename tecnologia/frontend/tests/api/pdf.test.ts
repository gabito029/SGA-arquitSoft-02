// Descarga y verificación de PDF (incremento 002: T030 y T041).
import { ErrorApi, EVENTO_SESION_EXPIRADA, fijarToken } from '../../src/api/cliente';
import { descargarPdf, rutaPdf, validarArchivoPdf, verificarPdf } from '../../src/api/pdf';
import { respuesta, simularFetch } from '../apoyo/respuestas';

function respuestaPdf(): Response {
  return {
    ok: true,
    status: 200,
    blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
  } as unknown as Response;
}

describe('api/pdf', () => {
  afterEach(() => fijarToken(null));

  it('arma la ruta del PDF del requerimiento y del acta', () => {
    expect(rutaPdf('r1', 'requerimiento')).toBe('/requerimientos/r1/documento.pdf');
    expect(rutaPdf('r1', 'acta')).toBe('/requerimientos/r1/acta/documento.pdf');
  });

  it('descarga el PDF con el token y lo guarda con un enlace temporal', async () => {
    fijarToken('tok');
    const fetchSimulado = simularFetch(respuestaPdf());
    const crear = jest.fn(() => 'blob:pdf');
    const revocar = jest.fn();
    Object.assign(URL, { createObjectURL: crear, revokeObjectURL: revocar });
    const clic = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    await descargarPdf('r1', 'acta', 'REQ-1-acta.pdf');

    const [url, opciones] = fetchSimulado.mock.calls[0];
    expect(url).toBe('/api/v1/requerimientos/r1/acta/documento.pdf');
    expect(opciones.headers).toMatchObject({
      Accept: 'application/pdf',
      Authorization: 'Bearer tok',
    });
    expect(crear).toHaveBeenCalled();
    expect(clic).toHaveBeenCalledTimes(1);
    expect(revocar).toHaveBeenCalledWith('blob:pdf');
    clic.mockRestore();
  });

  it('convierte los errores al mensaje en español y avisa del 401', async () => {
    fijarToken('tok');
    const escucha = jest.fn();
    window.addEventListener(EVENTO_SESION_EXPIRADA, escucha);
    simularFetch(respuesta(409, { codigo: 'SIN_FIRMAS', mensaje: 'Sin firmas todavía.' }));
    await expect(descargarPdf('r1', 'requerimiento', 'x.pdf')).rejects.toMatchObject({
      estado: 409,
      codigo: 'SIN_FIRMAS',
    });
    simularFetch(respuesta(401, { codigo: 'NO_AUTENTICADO', mensaje: 'x' }));
    await expect(descargarPdf('r1', 'requerimiento', 'x.pdf')).rejects.toBeInstanceOf(ErrorApi);
    expect(escucha).toHaveBeenCalledTimes(1);
    window.removeEventListener(EVENTO_SESION_EXPIRADA, escucha);
  });

  it('un fallo de red se informa como error de red', async () => {
    simularFetch(new Error('sin red'));
    await expect(verificarPdf(new Blob(['%PDF']))).rejects.toMatchObject({ codigo: 'ERROR_RED' });
  });

  it('envía el PDF como cuerpo application/pdf', async () => {
    const fetchSimulado = simularFetch(
      respuesta(200, { resultado: 'AUTENTICO', motivo: 'ok', documento: null }),
    );
    const archivo = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
    expect((await verificarPdf(archivo)).resultado).toBe('AUTENTICO');
    const [url, opciones] = fetchSimulado.mock.calls[0];
    expect(url).toBe('/api/v1/documentos/verificacion');
    expect(opciones.method).toBe('POST');
    expect(opciones.headers['Content-Type']).toBe('application/pdf');
    expect(opciones.body).toBe(archivo);
  });

  it('valida el archivo antes de enviarlo', () => {
    const pdf = (tamano: number, nombre = 'a.pdf', tipo = 'application/pdf') =>
      Object.defineProperty(new File(['x'], nombre, { type: tipo }), 'size', { value: tamano });
    expect(validarArchivoPdf(null)).toBe('Elija un archivo PDF.');
    expect(validarArchivoPdf(pdf(0))).toBe('El archivo está vacío.');
    expect(validarArchivoPdf(pdf(6 * 1024 * 1024))).toMatch(/5 MB/);
    expect(validarArchivoPdf(pdf(10, 'foto.png', 'image/png'))).toBe('El archivo no es un PDF.');
    expect(validarArchivoPdf(pdf(10, 'sin-tipo.PDF', ''))).toBeNull();
    expect(validarArchivoPdf(pdf(10))).toBeNull();
  });
});
