// T063: bandeja paginada con filtro por estado, carga y lista vacía.
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { fijarToken } from '../../src/api/cliente';
import { SesionProveedor } from '../../src/auth/SesionContexto';
import { Bandeja } from '../../src/paginas/Bandeja';
import { requerimiento } from '../apoyo/catalogo';
import { respuesta, simularFetch, token } from '../apoyo/respuestas';

function renderizar() {
  sessionStorage.setItem('sga.sesion', JSON.stringify(token()));
  return render(
    <SesionProveedor>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Bandeja />
      </MemoryRouter>
    </SesionProveedor>,
  );
}

afterEach(() => {
  sessionStorage.clear();
  fijarToken(null);
});

describe('Bandeja', () => {
  it('muestra una tabla con encabezados, fecha y la acción pendiente (T101)', async () => {
    simularFetch(
      respuesta(200, {
        items: [
          requerimiento({
            estado: 'PENDIENTE_VB_UNIDAD',
            acciones_disponibles: ['FIRMAR', 'RECHAZAR'],
            creado_en: '2026-11-23T10:00:00',
          }),
          requerimiento({ id: 'otra', codigo: 'REQ-2026-000002', acciones_disponibles: [] }),
        ],
        total: 2,
        page: 1,
        size: 20,
      }),
    );
    renderizar();
    const tabla = await screen.findByRole('table');
    const encabezados = within(tabla)
      .getAllByRole('columnheader')
      .map((c) => c.textContent);
    expect(encabezados).toEqual([
      'Código',
      'Categoría',
      'Unidad',
      'Fecha',
      'Estado',
      'Acción pendiente',
    ]);
    const [, primera, segunda] = within(tabla).getAllByRole('row');
    expect(within(primera).getByRole('link', { name: 'REQ-2026-000001' })).toBeInTheDocument();
    expect(primera).toHaveTextContent('Intendencia');
    expect(primera).toHaveTextContent('23/11/2026');
    expect(primera).toHaveTextContent('En visto bueno de la unidad');
    expect(within(primera).getByText('Por firmar')).toHaveClass('pendiente');
    expect(segunda).toHaveTextContent('—');
    // En celular cada celda lleva su etiqueta (se muestra con CSS).
    expect(within(primera).getAllByRole('cell')[3]).toHaveAttribute('data-etiqueta', 'Fecha');
  });

  it('muestra arriba un resumen de la cantidad de solicitudes por estado (T110)', async () => {
    const fetchSimulado = simularFetch(
      respuesta(200, {
        items: [
          requerimiento({ id: 'a', estado: 'PENDIENTE_VB_UNIDAD' }),
          requerimiento({ id: 'b', estado: 'PENDIENTE_APROBACION' }),
          requerimiento({ id: 'c', estado: 'CONFIRMADA' }),
          requerimiento({ id: 'd', estado: 'ANULADA' }),
        ],
        total: 4,
        page: 1,
        size: 20,
      }),
    );
    renderizar();
    const resumen = await screen.findByRole('region', { name: 'Resumen por estado' });
    const tarjetas = within(resumen)
      .getAllByRole('listitem')
      .map((t) => t.textContent);
    expect(tarjetas).toEqual(['2En trámite', '1Recibidas', '1Rechazadas o anuladas']);
    // El resumen sale de la página ya cargada: no hay llamadas nuevas a la API.
    expect(fetchSimulado).toHaveBeenCalledTimes(1);
  });

  it('muestra el estado de lista vacía', async () => {
    simularFetch(respuesta(200, { items: [], total: 0, page: 1, size: 20 }));
    renderizar();
    expect(await screen.findByText('No hay solicitudes para mostrar.')).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Resumen por estado' })).not.toBeInTheDocument();
  });

  it('filtra por estado y vuelve a la primera página', async () => {
    const vacia = { items: [], total: 0, page: 1, size: 20 };
    const fetchSimulado = simularFetch(respuesta(200, vacia), respuesta(200, vacia));
    renderizar();
    await screen.findByText('No hay solicitudes para mostrar.');
    await userEvent.setup().selectOptions(screen.getByLabelText('Estado'), 'PENDIENTE_VB_UNIDAD');

    await waitFor(() => expect(fetchSimulado).toHaveBeenCalledTimes(2));
    expect(fetchSimulado.mock.calls[1][0]).toBe(
      '/api/v1/requerimientos?page=1&size=20&estado=PENDIENTE_VB_UNIDAD',
    );
    expect(await screen.findByText('No hay solicitudes en este estado.')).toBeInTheDocument();
  });

  it('pagina cuando hay más de una página', async () => {
    const items = [requerimiento()];
    const fetchSimulado = simularFetch(
      respuesta(200, { items, total: 25, page: 1, size: 20 }),
      respuesta(200, { items, total: 25, page: 2, size: 20 }),
    );
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Siguiente' }));
    expect(await screen.findByText('Página 2 de 2')).toBeInTheDocument();
    expect(fetchSimulado.mock.calls[1][0]).toBe('/api/v1/requerimientos?page=2&size=20');
  });

  it('muestra el error de la API en español', async () => {
    simularFetch(new TypeError('sin red'));
    renderizar();
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar con el servidor');
  });
});
