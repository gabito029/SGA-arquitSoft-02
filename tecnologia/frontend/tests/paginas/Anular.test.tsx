// T086: el botón Anular solo aparece en BORRADOR y el motivo es obligatorio.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DetalleSolicitud } from '../../src/paginas/DetalleSolicitud';
import { requerimiento } from '../apoyo/catalogo';
import { respuesta, simularFetch } from '../apoyo/respuestas';

const ID = 'cccccccc-0000-0000-0000-000000000001';
const BORRADOR = requerimiento(); // acciones: EDITAR, ENVIAR, ANULAR

function renderizar() {
  return render(
    <MemoryRouter
      initialEntries={[`/solicitudes/${ID}`]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/solicitudes/:id" element={<DetalleSolicitud />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('Anular', () => {
  it('aparece en BORRADOR', async () => {
    simularFetch(respuesta(200, BORRADOR), respuesta(200, []));
    renderizar();
    expect(await screen.findByRole('button', { name: 'Anular' })).toBeInTheDocument();
  });

  it.each(['PENDIENTE_VB_UNIDAD', 'APROBADA', 'RECHAZADA'] as const)(
    'no aparece en %s',
    async (estado) => {
      simularFetch(respuesta(200, requerimiento({ estado, acciones_disponibles: [] })), respuesta(200, []));
      renderizar();
      await screen.findByRole('heading', { name: /REQ-2026-000001/ });
      expect(screen.queryByRole('button', { name: 'Anular' })).not.toBeInTheDocument();
    },
  );

  it('el motivo es obligatorio', async () => {
    const fetchSimulado = simularFetch(respuesta(200, BORRADOR), respuesta(200, []));
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Anular' }));
    await usuario.click(screen.getByRole('button', { name: 'Confirmar anulación' }));
    expect(screen.getByText('Indique el motivo.')).toBeInTheDocument();
    await usuario.type(screen.getByLabelText('Motivo'), 'abc');
    await usuario.click(screen.getByRole('button', { name: 'Confirmar anulación' }));
    expect(screen.getByText(/al menos 5/)).toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
  });

  it('anula con motivo y muestra la solicitud anulada', async () => {
    const anulada = requerimiento({ estado: 'ANULADA', acciones_disponibles: [] });
    const fetchSimulado = simularFetch(
      respuesta(200, BORRADOR),
      respuesta(200, []),
      respuesta(200, anulada),
      respuesta(200, anulada),
      respuesta(200, []),
    );
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Anular' }));
    await usuario.type(screen.getByLabelText('Motivo'), 'Material de guerra bloqueado');
    await usuario.click(screen.getByRole('button', { name: 'Confirmar anulación' }));

    expect(await screen.findByText(/Anuló la solicitud/)).toBeInTheDocument();
    const [url, opciones] = fetchSimulado.mock.calls[2];
    expect(url).toBe(`/api/v1/requerimientos/${ID}/anular`);
    expect(JSON.parse(opciones.body)).toEqual({ motivo: 'Material de guerra bloqueado' });
    expect(await screen.findByText('Anulada')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.queryByRole('button', { name: 'Anular' })).not.toBeInTheDocument();
  });

  it('cancelar cierra el diálogo sin enviar', async () => {
    const fetchSimulado = simularFetch(respuesta(200, BORRADOR), respuesta(200, []));
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Anular' }));
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
  });
});
