// T065: detalle con Firmar y Rechazar; fetch simulado.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { Firma } from '../../src/api/tipos';
import { DetalleSolicitud } from '../../src/paginas/DetalleSolicitud';
import { requerimiento } from '../apoyo/catalogo';
import { respuesta, simularFetch } from '../apoyo/respuestas';

const ID = 'cccccccc-0000-0000-0000-000000000001';
const PENDIENTE = requerimiento({
  estado: 'PENDIENTE_VB_UNIDAD',
  acciones_disponibles: ['FIRMAR', 'RECHAZAR'],
});
const FIRMA_VB: Firma = {
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

/** Pulsa Firmar y confirma en el diálogo propio de la página (T100). */
async function firmarConfirmando() {
  const usuario = userEvent.setup();
  await usuario.click(await screen.findByRole('button', { name: 'Firmar' }));
  await usuario.click(screen.getByRole('button', { name: 'Sí, firmar' }));
}

describe('DetalleSolicitud', () => {
  it('muestra Firmar y Rechazar solo si la API los permite', async () => {
    simularFetch(respuesta(200, PENDIENTE), respuesta(200, []));
    renderizar();
    expect(await screen.findByRole('button', { name: 'Firmar' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Rechazar' })).toBeInTheDocument();
  });

  it('no muestra acciones si no hay ninguna disponible', async () => {
    simularFetch(
      respuesta(200, requerimiento({ estado: 'PENDIENTE_CONFORMIDAD', acciones_disponibles: [] })),
      respuesta(200, [FIRMA_VB]),
    );
    renderizar();
    expect(await screen.findByText('En conformidad de la División/Brigada')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Firmar' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Rechazar' })).not.toBeInTheDocument();
    // Las firmas registradas se listan con su nivel y firmante.
    expect(screen.getByText('Visto bueno de la unidad')).toBeInTheDocument();
    expect(screen.getByText(/Aprobó: Comandante BIM-11/)).toBeInTheDocument();
  });

  it('muestra cada firma como un sello con cargo, fecha, hora y huella abreviada (T111)', async () => {
    simularFetch(
      respuesta(200, requerimiento({ estado: 'PENDIENTE_CONFORMIDAD', acciones_disponibles: [] })),
      respuesta(200, [{ ...FIRMA_VB, huella_sha256: `12345678${'0'.repeat(48)}abcdef90` }]),
    );
    renderizar();
    const sello = (await screen.findByText(/Aprobó: Comandante BIM-11/)).closest('li');
    expect(sello).toHaveClass('sello');
    expect(sello).toHaveTextContent('Comandante de la unidad · BIM-11');
    const momento = new Date(FIRMA_VB.firmado_en);
    const hora = `${String(momento.getHours()).padStart(2, '0')}:${String(momento.getMinutes()).padStart(2, '0')}`;
    expect(sello).toHaveTextContent(`Hora${hora}`);
    expect(sello).toHaveTextContent('12345678…abcdef90');
  });

  it('firma y después recarga el detalle', async () => {
    const siguiente = requerimiento({ estado: 'PENDIENTE_CONFORMIDAD', acciones_disponibles: [] });
    const fetchSimulado = simularFetch(
      respuesta(200, PENDIENTE),
      respuesta(200, []),
      respuesta(201, siguiente),
      respuesta(200, siguiente),
      respuesta(200, [FIRMA_VB]),
    );
    renderizar();
    await firmarConfirmando();

    expect(await screen.findByText(/Firmó la solicitud/)).toBeInTheDocument();
    const [url, opciones] = fetchSimulado.mock.calls[2];
    expect(url).toBe(`/api/v1/requerimientos/${ID}/firmas`);
    expect(opciones.method).toBe('POST');
    expect(JSON.parse(opciones.body)).toEqual({ decision: 'APROBAR' });
    // Recarga: detalle y firmas otra vez.
    await waitFor(() => expect(fetchSimulado).toHaveBeenCalledTimes(5));
    expect(fetchSimulado.mock.calls[3][0]).toBe(`/api/v1/requerimientos/${ID}`);
    expect(await screen.findByText(/Aprobó: Comandante BIM-11/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Firmar' })).not.toBeInTheDocument();
  });

  it('firmar pide confirmación en la página y cancelar no envía nada (T100)', async () => {
    const confirmar = jest.spyOn(window, 'confirm');
    const fetchSimulado = simularFetch(respuesta(200, PENDIENTE), respuesta(200, []));
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Firmar' }));

    const dialogo = screen.getByRole('alertdialog', { name: '¿Firmar la solicitud?' });
    expect(dialogo).toHaveTextContent('no se puede deshacer');
    expect(dialogo).toHaveTextContent('REQ-2026-000001');
    expect(dialogo).toHaveFocus();
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
    expect(confirmar).not.toHaveBeenCalled();
    confirmar.mockRestore();
  });

  it('Escape cierra la confirmación de la firma', async () => {
    simularFetch(respuesta(200, PENDIENTE), respuesta(200, []));
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Firmar' }));
    await usuario.keyboard('{Escape}');
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });

  it('el diálogo de rechazo advierte que no se puede deshacer', async () => {
    simularFetch(respuesta(200, PENDIENTE), respuesta(200, []));
    renderizar();
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Rechazar' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('no se puede deshacer');
  });

  it('muestra el mensaje que deja otra pantalla al llegar (T103)', async () => {
    simularFetch(respuesta(200, PENDIENTE), respuesta(200, []));
    render(
      <MemoryRouter
        initialEntries={[{ pathname: `/solicitudes/${ID}`, state: { exito: 'Solicitud enviada.' } }]}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route path="/solicitudes/:id" element={<DetalleSolicitud />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByText('Solicitud enviada.')).toBeInTheDocument();
  });

  it('muestra el monto en soles y las unidades en plural (T104)', async () => {
    simularFetch(respuesta(200, { ...PENDIENTE, monto_total: '1255.00' }), respuesta(200, []));
    renderizar();
    expect(await screen.findByText(/Monto: S\/ 1 255,00/)).toBeInTheDocument();
    expect(screen.getByText('2 unidades')).toBeInTheDocument();
  });

  it('rechazar sin motivo no envía nada', async () => {
    const fetchSimulado = simularFetch(respuesta(200, PENDIENTE), respuesta(200, []));
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Rechazar' }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    await usuario.click(screen.getByRole('button', { name: 'Confirmar rechazo' }));

    expect(screen.getByText('Indique el motivo.')).toBeInTheDocument();
    expect(fetchSimulado).toHaveBeenCalledTimes(2);
  });

  it('rechaza con motivo y cierra el diálogo', async () => {
    const rechazada = requerimiento({ estado: 'RECHAZADA', acciones_disponibles: [] });
    const fetchSimulado = simularFetch(
      respuesta(200, PENDIENTE),
      respuesta(200, []),
      respuesta(201, rechazada),
      respuesta(200, rechazada),
      respuesta(200, [{ ...FIRMA_VB, decision: 'RECHAZAR' }]),
    );
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Rechazar' }));
    await usuario.type(screen.getByLabelText('Motivo'), 'No corresponde a la dotación');
    await usuario.click(screen.getByRole('button', { name: 'Confirmar rechazo' }));

    expect(await screen.findByText('Rechazó la solicitud.')).toBeInTheDocument();
    expect(JSON.parse(fetchSimulado.mock.calls[2][1].body)).toEqual({
      decision: 'RECHAZAR',
      motivo: 'No corresponde a la dotación',
    });
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByText(/Rechazó: Comandante BIM-11/)).toBeInTheDocument();
  });

  it('un 409 muestra un mensaje comprensible y recarga el estado real', async () => {
    const cambiada = requerimiento({ estado: 'PENDIENTE_CONFORMIDAD', acciones_disponibles: [] });
    simularFetch(
      respuesta(200, PENDIENTE),
      respuesta(200, []),
      respuesta(409, { codigo: 'ESTADO_CAMBIADO', mensaje: 'Otro usuario cambió el requerimiento.' }),
      respuesta(200, cambiada),
      respuesta(200, [FIRMA_VB]),
    );
    renderizar();
    await firmarConfirmando();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Otra persona actuó sobre esta solicitud al mismo tiempo',
    );
    expect(await screen.findByText('En conformidad de la División/Brigada')).toBeInTheDocument();
  });

  it('NIVEL_YA_FIRMADO se explica en español', async () => {
    simularFetch(
      respuesta(200, PENDIENTE),
      respuesta(200, []),
      respuesta(409, { codigo: 'NIVEL_YA_FIRMADO', mensaje: 'x' }),
      respuesta(200, PENDIENTE),
      respuesta(200, []),
    );
    renderizar();
    await firmarConfirmando();
    expect(await screen.findByText('Este nivel ya firmó la solicitud.')).toBeInTheDocument();
  });

  it('muestra y oculta la línea de tiempo bajo demanda', async () => {
    const fetchSimulado = simularFetch(
      respuesta(200, PENDIENTE),
      respuesta(200, []),
      respuesta(200, [
        {
          accion: 'ENVIAR',
          estado_anterior: 'BORRADOR',
          estado_nuevo: 'PENDIENTE_VB_UNIDAD',
          usuario: 'Oficial de logística BIM-11',
          rol: 'OFICIAL_LOGISTICA',
          organo: { id: 'u1', codigo: 'BIM-11', nombre: 'BIM N.° 11' },
          ocurrido_en: '2026-11-24T10:00:00Z',
        },
      ]),
    );
    renderizar();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole('button', { name: 'Ver línea de tiempo' }));
    expect(await screen.findByText('Envió la solicitud')).toBeInTheDocument();
    expect(fetchSimulado.mock.calls[2][0]).toBe(`/api/v1/requerimientos/${ID}/historial`);
    await usuario.click(screen.getByRole('button', { name: 'Ocultar línea de tiempo' }));
    expect(screen.queryByText('Envió la solicitud')).not.toBeInTheDocument();
  });

  it('muestra el error si la línea de tiempo no carga', async () => {
    simularFetch(respuesta(200, PENDIENTE), respuesta(200, []), new TypeError('sin red'));
    renderizar();
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Ver línea de tiempo' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar');
  });

  it('una solicitud ajena muestra el 404 en español', async () => {
    simularFetch(
      respuesta(404, {
        codigo: 'NO_ENCONTRADO',
        mensaje: 'La solicitud no existe o no pertenece a su jurisdicción.',
      }),
      respuesta(404, { codigo: 'NO_ENCONTRADO', mensaje: 'x' }),
    );
    renderizar();
    expect(await screen.findByRole('alert')).toHaveTextContent('no pertenece a su jurisdicción');
  });
});
