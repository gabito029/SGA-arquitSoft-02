// T080: las diferencias se resaltan; ALTERADA se muestra como alerta e INTEGRA como éxito.
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { Firma, Verificacion } from '../../src/api/tipos';
import { DetalleSolicitud } from '../../src/paginas/DetalleSolicitud';
import { ITEM_INT_1, ITEM_INT_2, requerimiento } from '../apoyo/catalogo';
import { respuesta, simularFetch } from '../apoyo/respuestas';

const ID = 'cccccccc-0000-0000-0000-000000000001';
const EN_TRANSITO = requerimiento({
  estado: 'EN_TRANSITO',
  items: [
    { item: ITEM_INT_1, cantidad_solicitada: 10, cantidad_despachada: 10 },
    { item: ITEM_INT_2, cantidad_solicitada: 5, cantidad_despachada: 4 },
  ],
  acciones_disponibles: ['FIRMAR_ACTA'],
});
const FIRMA: Firma = {
  id: 'f1',
  nivel: 'VB_UNIDAD',
  decision: 'APROBAR',
  firmante: 'Comandante BIM-11',
  rol: 'COMANDANTE_UNIDAD',
  organo: { id: 'u1', codigo: 'BIM-11', nombre: 'BIM N.° 11' },
  huella_sha256: 'a'.repeat(64),
  metodo: 'ed25519-sha256-v1',
  firmado_en: '2026-11-24T10:00:00Z',
};

function verificacion(resultado: 'INTEGRA' | 'ALTERADA'): Verificacion {
  return {
    requerimiento_id: ID,
    resultado,
    firmas: [
      {
        firma_id: 'f1',
        nivel: 'VB_UNIDAD',
        resultado: 'INTEGRA',
        firmante: 'Comandante BIM-11',
        firmado_en: '2026-11-24T10:00:00Z',
      },
      {
        firma_id: 'f4',
        nivel: 'ACTA_RECEPCION',
        resultado,
        firmante: 'Oficial de logística BIM-11',
        firmado_en: '2026-11-24T12:00:00Z',
      },
    ],
  };
}

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

describe('Acta de recepción', () => {
  it('resalta las líneas con diferencias entre lo despachado y lo recibido', async () => {
    simularFetch(respuesta(200, EN_TRANSITO), respuesta(200, [FIRMA]));
    renderizar();
    await screen.findByRole('heading', { name: 'Firmar acta de recepción' });
    // Por defecto se propone lo despachado: sin diferencias.
    expect(screen.getByTestId('linea-INT-001')).not.toHaveClass('acta__linea--diferencia');
    expect(screen.getByText('Lo recibido coincide con lo despachado.')).toBeInTheDocument();

    const usuario = userEvent.setup();
    const campo = screen.getByLabelText('INT-001 — recibido (despachado: 10 unidades)');
    await usuario.clear(campo);
    await usuario.type(campo, '8');
    const linea = screen.getByTestId('linea-INT-001');
    expect(linea).toHaveClass('acta__linea--diferencia');
    expect(within(linea).getByText('Diferencia con lo despachado')).toBeInTheDocument();
    expect(screen.getByText('1 ítem(s) con diferencias.')).toBeInTheDocument();
  });

  it('firma el acta con lo recibido y las observaciones', async () => {
    const confirmada = { ...EN_TRANSITO, estado: 'CONFIRMADA' as const, acciones_disponibles: [] };
    const fetchSimulado = simularFetch(
      respuesta(200, EN_TRANSITO),
      respuesta(200, [FIRMA]),
      respuesta(201, { id: 'a1', tiene_diferencias: true }),
      respuesta(200, confirmada),
      respuesta(200, [FIRMA]),
    );
    renderizar();
    await screen.findByRole('heading', { name: 'Firmar acta de recepción' });
    const usuario = userEvent.setup();
    await usuario.type(screen.getByLabelText('INT-002 — observación'), 'Falta una unidad');
    await usuario.click(screen.getByRole('button', { name: 'Firmar acta' }));
    // T100: confirmación dentro de la página antes de firmar.
    const dialogo = screen.getByRole('alertdialog', { name: '¿Firmar el acta de recepción?' });
    expect(dialogo).toHaveTextContent('no se puede deshacer');
    expect(dialogo).toHaveTextContent('Lo recibido coincide con lo despachado.');
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
    await usuario.click(screen.getByRole('button', { name: 'Sí, firmar el acta' }));

    expect(await screen.findByText(/Acta firmada con diferencias/)).toBeInTheDocument();
    const [url, opciones] = fetchSimulado.mock.calls[2];
    expect(url).toBe(`/api/v1/requerimientos/${ID}/acta`);
    expect(JSON.parse(opciones.body)).toEqual({
      items: [
        { item_id: ITEM_INT_1.id, cantidad_recibida: 10 },
        { item_id: ITEM_INT_2.id, cantidad_recibida: 4, observacion: 'Falta una unidad' },
      ],
    });
  });

  it('cancelar la confirmación del acta no firma', async () => {
    const fetchSimulado = simularFetch(respuesta(200, EN_TRANSITO), respuesta(200, [FIRMA]));
    renderizar();
    await screen.findByRole('heading', { name: 'Firmar acta de recepción' });
    const usuario = userEvent.setup();
    await usuario.click(screen.getByRole('button', { name: 'Firmar acta' }));
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
  });

  it('no firma con cantidades inválidas', async () => {
    const fetchSimulado = simularFetch(respuesta(200, EN_TRANSITO), respuesta(200, [FIRMA]));
    renderizar();
    await screen.findByRole('heading', { name: 'Firmar acta de recepción' });
    const usuario = userEvent.setup();
    await usuario.clear(screen.getByLabelText('INT-001 — recibido (despachado: 10 unidades)'));
    await usuario.click(screen.getByRole('button', { name: 'Firmar acta' }));
    expect(screen.getByText('Indique un número entero mayor o igual a 0.')).toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
  });

  it('INTEGRA se muestra como éxito, con firmante y fecha', async () => {
    simularFetch(
      respuesta(200, { ...EN_TRANSITO, estado: 'CONFIRMADA', acciones_disponibles: [] }),
      respuesta(200, [FIRMA]),
      respuesta(200, verificacion('INTEGRA')),
    );
    renderizar();
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Verificar' }));

    const mensaje = await screen.findByText('Todas las firmas están íntegras.');
    expect(mensaje.closest('.mensaje')).toHaveClass('mensaje--exito');
    expect(screen.getAllByText('Íntegra')).toHaveLength(2);
    expect(screen.getByText('Oficial de logística BIM-11')).toBeInTheDocument();
  });

  it('ALTERADA se muestra como alerta', async () => {
    simularFetch(
      respuesta(200, { ...EN_TRANSITO, estado: 'CONFIRMADA', acciones_disponibles: [] }),
      respuesta(200, [FIRMA]),
      respuesta(200, verificacion('ALTERADA')),
    );
    renderizar();
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Verificar' }));

    const alerta = await screen.findByRole('alert');
    expect(alerta).toHaveTextContent('Se detectó una alteración');
    expect(alerta).toHaveClass('mensaje--error');
    expect(screen.getByText('Alterada')).toHaveClass('estado--alerta');
  });

  it('muestra el error si la verificación falla', async () => {
    simularFetch(
      respuesta(200, { ...EN_TRANSITO, estado: 'CONFIRMADA', acciones_disponibles: [] }),
      respuesta(200, [FIRMA]),
      respuesta(404, { codigo: 'NO_ENCONTRADO', mensaje: 'No existe.' }),
    );
    renderizar();
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Verificar' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('No existe.');
  });
});
