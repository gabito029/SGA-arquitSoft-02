// T040: verificar un PDF subido (incremento 002, US5; EQ-02).
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { VerificacionPdf } from '../../src/api/tipos';
import { VerificarDocumento } from '../../src/paginas/VerificarDocumento';
import { SELLO_VB } from '../apoyo/documento';
import { respuesta, simularFetch } from '../apoyo/respuestas';

const AUTENTICO: VerificacionPdf = {
  resultado: 'AUTENTICO',
  motivo: 'El documento fue emitido por el SGA, no tiene cambios y sus firmas siguen íntegras.',
  documento: {
    codigo_verificacion: 'SGA-ABCD-EFGH-JKLM',
    tipo: 'REQUERIMIENTO',
    requerimiento_id: 'r1',
    requerimiento_codigo: 'REQ-2026-000001',
    emitido_en: '2026-11-24T12:00:00Z',
    sellos: [SELLO_VB],
  },
};

function renderizar() {
  render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <VerificarDocumento />
    </MemoryRouter>,
  );
}

function pdf(nombre = 'req.pdf', tipo = 'application/pdf') {
  return new File(['%PDF-1.4 contenido'], nombre, { type: tipo });
}

async function subirYVerificar(archivo: File) {
  const usuario = userEvent.setup({ applyAccept: false });
  await usuario.upload(screen.getByLabelText(/Archivo PDF/), archivo);
  await usuario.click(screen.getByRole('button', { name: 'Verificar' }));
}

describe('VerificarDocumento', () => {
  it('muestra "Auténtico" con el código, el requerimiento y los sellos', async () => {
    const fetchSimulado = simularFetch(respuesta(200, AUTENTICO));
    renderizar();
    await subirYVerificar(pdf());
    const resultado = await screen.findByRole('region', { name: /Auténtico/ });
    expect(resultado).toHaveTextContent('SGA-ABCD-EFGH-JKLM');
    expect(resultado).toHaveTextContent('REQ-2026-000001');
    expect(resultado).toHaveTextContent('Visto bueno de la unidad: aprobó Comandante BIM-11');
    expect(screen.getByRole('link', { name: 'REQ-2026-000001' })).toHaveAttribute(
      'href',
      '/solicitudes/r1',
    );
    expect(fetchSimulado.mock.calls[0][1].headers['Content-Type']).toBe('application/pdf');
  });

  it('muestra "Alterado" con el motivo', async () => {
    simularFetch(
      respuesta(200, {
        resultado: 'ALTERADO',
        motivo: 'El archivo no coincide con el documento emitido.',
        documento: null,
      }),
    );
    renderizar();
    await subirYVerificar(pdf());
    const resultado = await screen.findByRole('region', { name: /Alterado/ });
    expect(resultado).toHaveTextContent('El archivo no coincide con el documento emitido.');
  });

  it('un archivo que no es PDF no se envía', async () => {
    const fetchSimulado = simularFetch();
    renderizar();
    await subirYVerificar(pdf('foto.png', 'image/png'));
    expect(await screen.findByRole('alert')).toHaveTextContent('El archivo no es un PDF.');
    expect(fetchSimulado).not.toHaveBeenCalled();
  });

  it('sin archivo pide elegir uno', async () => {
    renderizar();
    await userEvent.setup().click(screen.getByRole('button', { name: 'Verificar' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Elija un archivo PDF.');
  });

  it('muestra el error de la API (404 de otra jurisdicción)', async () => {
    simularFetch(
      respuesta(404, { codigo: 'NO_ENCONTRADO', mensaje: 'No existe o no es de su jurisdicción.' }),
    );
    renderizar();
    await subirYVerificar(pdf());
    expect(await screen.findByRole('alert')).toHaveTextContent('No existe o no es de su jurisdicción.');
  });
});
