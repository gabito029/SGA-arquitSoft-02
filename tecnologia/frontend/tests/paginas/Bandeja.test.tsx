// T063: bandeja paginada con filtro por estado, carga y lista vacía.
import { render, screen, waitFor } from '@testing-library/react';
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
  it('lista las solicitudes con su estado y lo pendiente', async () => {
    simularFetch(
      respuesta(200, {
        items: [requerimiento({ estado: 'PENDIENTE_VB_UNIDAD', acciones_disponibles: ['FIRMAR', 'RECHAZAR'] })],
        total: 1,
        page: 1,
        size: 20,
      }),
    );
    renderizar();
    expect(await screen.findByRole('link', { name: 'REQ-2026-000001' })).toBeInTheDocument();
    expect(screen.getByText('En visto bueno de la unidad', { selector: '.estado' })).toBeInTheDocument();
    expect(screen.getByText('Pendiente: Firmar, Rechazar')).toBeInTheDocument();
  });

  it('muestra el estado de lista vacía', async () => {
    simularFetch(respuesta(200, { items: [], total: 0, page: 1, size: 20 }));
    renderizar();
    expect(await screen.findByText('No hay solicitudes para mostrar.')).toBeInTheDocument();
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
