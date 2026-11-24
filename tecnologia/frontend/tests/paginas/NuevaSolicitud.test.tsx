// T054: nueva solicitud con fetch simulado (bloqueo del COLOGE, errores 422 por campo y carga).
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation, useParams } from 'react-router-dom';
import { NuevaSolicitud } from '../../src/paginas/NuevaSolicitud';
import { ITEM_INT_1, ITEM_INT_2, requerimiento } from '../apoyo/catalogo';
import { respuesta, simularFetch } from '../apoyo/respuestas';

const CATALOGO = [ITEM_INT_1, ITEM_INT_2];

function renderizar() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <NuevaSolicitud />
    </MemoryRouter>,
  );
}

/** Detalle simulado: muestra el id de la ruta y el mensaje recibido en el estado de navegación. */
function DetalleSimulado() {
  const { id } = useParams();
  const { state } = useLocation();
  return (
    <p data-testid="detalle">
      {id} {(state as { exito?: string } | null)?.exito}
    </p>
  );
}

function renderizarConDetalle() {
  return render(
    <MemoryRouter
      initialEntries={['/solicitudes/nueva']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/solicitudes/nueva" element={<NuevaSolicitud />} />
        <Route path="/solicitudes/:id" element={<DetalleSimulado />} />
      </Routes>
    </MemoryRouter>,
  );
}

async function agregarItem(usuario: ReturnType<typeof userEvent.setup>, id: string, cantidad: string) {
  await usuario.selectOptions(screen.getByLabelText('Ítem'), id);
  const campo = screen.getByLabelText('Cantidad');
  await usuario.clear(campo);
  await usuario.type(campo, cantidad);
  await usuario.click(screen.getByRole('button', { name: 'Agregar ítem' }));
}

async function listo() {
  // Espera a que cargue el catálogo (primera llamada de fetch).
  await screen.findByRole('option', { name: /INT-001/ });
}

describe('NuevaSolicitud', () => {
  it('muestra 5 campos como máximo (FR-005)', async () => {
    simularFetch(respuesta(200, CATALOGO));
    const { container } = renderizar();
    await listo();
    expect(container.querySelectorAll('input, select, textarea').length).toBeLessThanOrEqual(5);
  });

  it('muestra la cantidad con la unidad en plural (T104)', async () => {
    simularFetch(respuesta(200, CATALOGO));
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await agregarItem(usuario, ITEM_INT_1.id, '1');
    expect(screen.getByText('1 unidad')).toBeInTheDocument();
    await agregarItem(usuario, ITEM_INT_2.id, '3');
    expect(screen.getByText('3 unidades')).toBeInTheDocument();
  });

  it('pide el catálogo de la categoría elegida', async () => {
    const fetchSimulado = simularFetch(respuesta(200, CATALOGO));
    renderizar();
    await listo();
    expect(fetchSimulado.mock.calls[0][0]).toBe('/api/v1/catalogo/items?categoria=INTENDENCIA');
  });

  it('no guarda sin ítems y lo indica', async () => {
    const fetchSimulado = simularFetch(respuesta(200, CATALOGO));
    renderizar();
    await listo();
    await userEvent.setup().click(screen.getByRole('button', { name: 'Guardar' }));
    expect(screen.getByText('Agregue al menos un ítem.')).toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(1);
  });

  it('valida la cantidad antes de agregar el ítem', async () => {
    simularFetch(respuesta(200, CATALOGO));
    renderizar();
    await listo();
    await agregarItem(userEvent.setup(), ITEM_INT_1.id, '0');
    expect(screen.getByText('La cantidad debe ser un número entero mayor que 0.')).toBeInTheDocument();
    expect(screen.getByText('Ítems (0)')).toBeInTheDocument();
  });

  it('al enviar va al detalle de la solicitud con el mensaje de éxito (T103)', async () => {
    const fetchSimulado = simularFetch(
      respuesta(200, CATALOGO),
      respuesta(201, requerimiento()),
      respuesta(200, requerimiento({ estado: 'PENDIENTE_VB_UNIDAD', acciones_disponibles: [] })),
    );
    renderizarConDetalle();
    await listo();
    const usuario = userEvent.setup();
    await agregarItem(usuario, ITEM_INT_1.id, '2');
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }));

    const detalle = await screen.findByTestId('detalle');
    expect(detalle).toHaveTextContent('cccccccc-0000-0000-0000-000000000001');
    expect(detalle).toHaveTextContent(
      'Solicitud REQ-2026-000001 enviada por el conducto regular.',
    );
    const [urlCrear, crear] = fetchSimulado.mock.calls[1];
    expect(urlCrear).toBe('/api/v1/requerimientos');
    expect(JSON.parse(crear.body)).toEqual({ items: [{ item_id: ITEM_INT_1.id, cantidad: 2 }] });
    expect(fetchSimulado.mock.calls[2][0]).toBe(
      '/api/v1/requerimientos/cccccccc-0000-0000-0000-000000000001/enviar',
    );
  });

  it('el envío bloqueado muestra el aviso del COLOGE y la deja Registrada', async () => {
    simularFetch(
      respuesta(200, CATALOGO),
      respuesta(201, requerimiento()),
      respuesta(409, {
        codigo: 'REQUIERE_COLOGE',
        mensaje: 'Requiere autorización del COLOGE (disponible en un próximo incremento).',
      }),
    );
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await agregarItem(usuario, ITEM_INT_1.id, '2');
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }));

    const aviso = await screen.findByText(/Requiere autorización del COLOGE/);
    expect(aviso.closest('.mensaje')).toHaveClass('mensaje--aviso');
    expect(screen.getByText('Registrada')).toBeInTheDocument();
  });

  it('muestra los errores 422 junto a cada línea', async () => {
    simularFetch(
      respuesta(200, CATALOGO),
      respuesta(422, {
        codigo: 'VALIDACION',
        mensaje: 'Los datos enviados no son válidos.',
        detalles: [{ campo: 'items.0.item_id', mensaje: 'El ítem está inactivo en el catálogo.' }],
      }),
    );
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await agregarItem(usuario, ITEM_INT_1.id, '2');
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }));

    expect(await screen.findByText('El ítem está inactivo en el catálogo.')).toBeInTheDocument();
    expect(screen.getByText('Los datos enviados no son válidos.')).toBeInTheDocument();
  });

  it('desactiva los botones mientras espera la respuesta', async () => {
    let resolver: (r: Response) => void = () => undefined;
    const fetchSimulado = jest
      .fn()
      .mockResolvedValueOnce(respuesta(200, CATALOGO))
      .mockImplementationOnce(() => new Promise<Response>((r) => (resolver = r)));
    globalThis.fetch = fetchSimulado as unknown as typeof fetch;
    renderizar();
    await listo();
    const usuario = userEvent.setup();
    await agregarItem(usuario, ITEM_INT_1.id, '2');
    await usuario.click(screen.getByRole('button', { name: 'Guardar' }));

    expect(screen.getByRole('button', { name: 'Guardando…' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Procesando la solicitud…');
    resolver(respuesta(201, requerimiento()));
    expect(await screen.findByText(/Solicitud REQ-2026-000001 guardada/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Guardar' })).toBeEnabled());
  });
});
