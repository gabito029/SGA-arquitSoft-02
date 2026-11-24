// T072: tabla paginada del stock del almacén.
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Stock } from '../../src/paginas/Stock';
import { ITEM_INT_1 } from '../apoyo/catalogo';
import { respuesta, simularFetch } from '../apoyo/respuestas';

function renderizar() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Stock />
    </MemoryRouter>,
  );
}

describe('Stock', () => {
  it('muestra el stock en una tabla y pagina', async () => {
    const fila = { item: ITEM_INT_1, cantidad: 494 };
    const fetchSimulado = simularFetch(
      respuesta(200, { items: [fila], total: 25, page: 1, size: 20 }),
      respuesta(200, { items: [fila], total: 25, page: 2, size: 20 }),
    );
    renderizar();
    expect(await screen.findByRole('cell', { name: '494 unidad' })).toBeInTheDocument();
    expect(fetchSimulado.mock.calls[0][0]).toBe('/api/v1/inventario/stock?page=1&size=20');
    await userEvent.setup().click(screen.getByRole('button', { name: 'Siguiente' }));
    expect(await screen.findByText('Página 2 de 2')).toBeInTheDocument();
  });

  it('indica cuando no hay stock y muestra los errores', async () => {
    simularFetch(respuesta(200, { items: [], total: 0, page: 1, size: 20 }));
    renderizar();
    expect(await screen.findByText('El almacén no tiene stock registrado.')).toBeInTheDocument();
  });

  it('muestra el 403 en español', async () => {
    simularFetch(respuesta(403, { codigo: 'SIN_PERMISO', mensaje: 'Su rol no permite realizar esta acción.' }));
    renderizar();
    expect(await screen.findByRole('alert')).toHaveTextContent('Su rol no permite');
  });
});
