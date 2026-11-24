// T073: el despacho no deja superar lo solicitado y STOCK_INSUFICIENTE muestra su mensaje.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DetalleSolicitud } from '../../src/paginas/DetalleSolicitud';
import { ITEM_INT_1, ITEM_INT_2, requerimiento } from '../apoyo/catalogo';
import { respuesta, simularFetch } from '../apoyo/respuestas';

const ID = 'cccccccc-0000-0000-0000-000000000001';
const APROBADA = requerimiento({
  estado: 'APROBADA',
  items: [
    { item: ITEM_INT_1, cantidad_solicitada: 7 },
    { item: ITEM_INT_2, cantidad_solicitada: 3 },
  ],
  acciones_disponibles: ['DESPACHAR'],
});

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

function campo(codigo: string) {
  return screen.getByLabelText(new RegExp(`^${codigo} —`));
}

describe('Despacho', () => {
  it('propone lo solicitado y lo usa como máximo', async () => {
    simularFetch(respuesta(200, APROBADA), respuesta(200, []));
    renderizar();
    await screen.findByRole('heading', { name: 'Despachar' });
    expect(campo('INT-001')).toHaveValue(7);
    expect(campo('INT-001')).toHaveAttribute('max', '7');
    expect(campo('INT-002')).toHaveValue(3);
  });

  it('no deja enviar una cantidad mayor que la solicitada', async () => {
    const fetchSimulado = simularFetch(respuesta(200, APROBADA), respuesta(200, []));
    renderizar();
    await screen.findByRole('heading', { name: 'Despachar' });
    const usuario = userEvent.setup();
    await usuario.clear(campo('INT-001'));
    await usuario.type(campo('INT-001'), '8');
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));

    expect(screen.getByText('No puede superar lo solicitado (7).')).toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
  });

  it('no deja despachar todo en cero', async () => {
    const fetchSimulado = simularFetch(respuesta(200, APROBADA), respuesta(200, []));
    renderizar();
    await screen.findByRole('heading', { name: 'Despachar' });
    const usuario = userEvent.setup();
    for (const codigo of ['INT-001', 'INT-002']) {
      await usuario.clear(campo(codigo));
      await usuario.type(campo(codigo), '0');
    }
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));
    expect(screen.getByText(/al menos un ítem/)).toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
  });

  it('despacha las cantidades indicadas y recarga', async () => {
    const enTransito = requerimiento({
      ...APROBADA,
      estado: 'EN_TRANSITO',
      items: [
        { item: ITEM_INT_1, cantidad_solicitada: 7, cantidad_despachada: 5 },
        { item: ITEM_INT_2, cantidad_solicitada: 3, cantidad_despachada: 3 },
      ],
      acciones_disponibles: [],
    });
    const fetchSimulado = simularFetch(
      respuesta(200, APROBADA),
      respuesta(200, []),
      respuesta(201, enTransito),
      respuesta(200, enTransito),
      respuesta(200, []),
    );
    renderizar();
    await screen.findByRole('heading', { name: 'Despachar' });
    const usuario = userEvent.setup();
    await usuario.clear(campo('INT-001'));
    await usuario.type(campo('INT-001'), '5');
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));

    expect(await screen.findByText(/Despacho registrado/)).toBeInTheDocument();
    const [url, opciones] = fetchSimulado.mock.calls[2];
    expect(url).toBe(`/api/v1/requerimientos/${ID}/despacho`);
    expect(JSON.parse(opciones.body)).toEqual({
      items: [
        { item_id: ITEM_INT_1.id, cantidad: 5 },
        { item_id: ITEM_INT_2.id, cantidad: 3 },
      ],
    });
    await waitFor(() =>
      expect(screen.queryByRole('heading', { name: 'Despachar' })).not.toBeInTheDocument(),
    );
    expect(screen.getByText('Despachado: 5')).toBeInTheDocument();
  });

  it('STOCK_INSUFICIENTE muestra un mensaje claro', async () => {
    simularFetch(
      respuesta(200, APROBADA),
      respuesta(200, []),
      respuesta(409, {
        codigo: 'STOCK_INSUFICIENTE',
        mensaje: 'No hay stock suficiente.',
        detalles: [{ campo: 'items.x', mensaje: 'Stock disponible: 3; solicitado: 7.' }],
      }),
      respuesta(200, APROBADA),
      respuesta(200, []),
    );
    renderizar();
    await screen.findByRole('heading', { name: 'Despachar' });
    await userEvent.setup().click(screen.getByRole('button', { name: 'Confirmar despacho' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No hay stock suficiente en el almacén para despachar estas cantidades.',
    );
  });
});
