// T073, T100 y T105: el despacho no deja superar lo solicitado, muestra el stock disponible,
// pide confirmación dentro de la página y STOCK_INSUFICIENTE muestra su mensaje.
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
// Stock del almacén: 10 raciones y 1 uniforme.
const STOCK = respuesta(200, {
  items: [
    { item: ITEM_INT_1, cantidad: 10 },
    { item: ITEM_INT_2, cantidad: 1 },
  ],
  total: 2,
  page: 1,
  size: 50,
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

async function listo() {
  await screen.findByText('Stock disponible: 10 unidades');
}

describe('Despacho', () => {
  it('propone lo solicitado, lo usa como máximo y muestra el stock disponible', async () => {
    const fetchSimulado = simularFetch(respuesta(200, APROBADA), respuesta(200, []), STOCK);
    renderizar();
    await listo();
    expect(fetchSimulado.mock.calls[2][0]).toBe('/api/v1/inventario/stock?page=1&size=50');
    expect(campo('INT-001')).toHaveValue(7);
    expect(campo('INT-001')).toHaveAttribute('max', '7');
    expect(campo('INT-001')).toHaveAccessibleDescription('Stock disponible: 10 unidades');
    expect(screen.getByText('Stock disponible: 1 unidad')).toBeInTheDocument();
    // Se proponen 3 uniformes y solo hay 1: se avisa antes de despachar.
    expect(screen.getByText(/supera el stock disponible/)).toBeInTheDocument();
  });

  it('indica cuando el stock no se pudo consultar', async () => {
    simularFetch(respuesta(200, APROBADA), respuesta(200, []), new TypeError('sin red'));
    renderizar();
    expect(
      await screen.findAllByText('Stock disponible: sin registro en el almacén'),
    ).toHaveLength(2);
  });

  it('no deja enviar una cantidad mayor que la solicitada', async () => {
    const fetchSimulado = simularFetch(respuesta(200, APROBADA), respuesta(200, []), STOCK);
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await usuario.clear(campo('INT-001'));
    await usuario.type(campo('INT-001'), '8');
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));

    expect(screen.getByText('No puede superar lo solicitado (7).')).toBeInTheDocument();
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(3);
  });

  it('no deja despachar todo en cero', async () => {
    const fetchSimulado = simularFetch(respuesta(200, APROBADA), respuesta(200, []), STOCK);
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    for (const codigo of ['INT-001', 'INT-002']) {
      await usuario.clear(campo(codigo));
      await usuario.type(campo(codigo), '0');
    }
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));
    expect(screen.getByText(/al menos un ítem/)).toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(3);
  });

  it('pide confirmación y cancelar no despacha', async () => {
    const fetchSimulado = simularFetch(respuesta(200, APROBADA), respuesta(200, []), STOCK);
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));

    const dialogo = screen.getByRole('alertdialog', { name: '¿Despachar estas cantidades?' });
    expect(dialogo).toHaveTextContent('no se puede deshacer');
    expect(dialogo).toHaveTextContent('INT-001 — Ración de campaña: 7 unidades');
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(3);
  });

  it('despacha las cantidades confirmadas y recarga', async () => {
    const enTransito = requerimiento({
      ...APROBADA,
      estado: 'EN_TRANSITO',
      items: [
        { item: ITEM_INT_1, cantidad_solicitada: 7, cantidad_despachada: 5 },
        { item: ITEM_INT_2, cantidad_solicitada: 3, cantidad_despachada: 1 },
      ],
      acciones_disponibles: [],
    });
    const fetchSimulado = simularFetch(
      respuesta(200, APROBADA),
      respuesta(200, []),
      STOCK,
      respuesta(201, enTransito),
      respuesta(200, enTransito),
      respuesta(200, []),
    );
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await usuario.clear(campo('INT-001'));
    await usuario.type(campo('INT-001'), '5');
    await usuario.clear(campo('INT-002'));
    await usuario.type(campo('INT-002'), '1');
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));
    await usuario.click(screen.getByRole('button', { name: 'Sí, despachar' }));

    expect(await screen.findByText(/Despacho registrado/)).toBeInTheDocument();
    const [url, opciones] = fetchSimulado.mock.calls[3];
    expect(url).toBe(`/api/v1/requerimientos/${ID}/despacho`);
    expect(JSON.parse(opciones.body)).toEqual({
      items: [
        { item_id: ITEM_INT_1.id, cantidad: 5 },
        { item_id: ITEM_INT_2.id, cantidad: 1 },
      ],
    });
    await waitFor(() =>
      expect(screen.queryByRole('heading', { name: 'Despachar' })).not.toBeInTheDocument(),
    );
    expect(screen.getByText('Despachado: 5 unidades')).toBeInTheDocument();
    expect(screen.getByText('Despachado: 1 unidad')).toBeInTheDocument();
  });

  it('STOCK_INSUFICIENTE muestra un mensaje claro y cierra la confirmación', async () => {
    simularFetch(
      respuesta(200, APROBADA),
      respuesta(200, []),
      STOCK,
      respuesta(409, {
        codigo: 'STOCK_INSUFICIENTE',
        mensaje: 'No hay stock suficiente.',
        detalles: [{ campo: 'items.x', mensaje: 'Stock disponible: 1; solicitado: 3.' }],
      }),
      respuesta(200, APROBADA),
      respuesta(200, []),
    );
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await usuario.click(screen.getByRole('button', { name: 'Confirmar despacho' }));
    await usuario.click(screen.getByRole('button', { name: 'Sí, despachar' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No hay stock suficiente en el almacén para despachar estas cantidades.',
    );
    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument());
  });
});
