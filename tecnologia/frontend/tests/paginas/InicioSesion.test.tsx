// T054: pantalla de inicio de sesión con fetch simulado.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { CLAVE_ALMACENAMIENTO, SesionProveedor } from '../../src/auth/SesionContexto';
import { InicioSesion } from '../../src/paginas/InicioSesion';
import { respuesta, simularFetch, token } from '../apoyo/respuestas';

function renderizar() {
  return render(
    <SesionProveedor>
      <MemoryRouter initialEntries={['/ingresar']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/ingresar" element={<InicioSesion />} />
          <Route path="/bandeja" element={<p>Bandeja de solicitudes</p>} />
        </Routes>
      </MemoryRouter>
    </SesionProveedor>,
  );
}

async function ingresar(usuario: string, contrasena: string) {
  const usuarioEvento = userEvent.setup();
  await usuarioEvento.type(screen.getByLabelText('Usuario'), usuario);
  await usuarioEvento.type(screen.getByLabelText('Contraseña'), contrasena);
  await usuarioEvento.click(screen.getByRole('button', { name: 'Ingresar' }));
}

afterEach(() => sessionStorage.clear());

describe('InicioSesion', () => {
  it('con credenciales correctas guarda la sesión y va a la bandeja', async () => {
    const fetchSimulado = simularFetch(respuesta(200, token()));
    renderizar();
    await ingresar('oficial.bim11', 'secreta');

    expect(await screen.findByText('Bandeja de solicitudes')).toBeInTheDocument();
    const [url, opciones] = fetchSimulado.mock.calls[0];
    expect(url).toBe('/api/v1/auth/login');
    expect(JSON.parse(opciones.body)).toEqual({ usuario: 'oficial.bim11', contrasena: 'secreta' });
    expect(sessionStorage.getItem(CLAVE_ALMACENAMIENTO)).toContain('token-de-prueba');
  });

  it('con credenciales erróneas muestra el mensaje y sigue en la pantalla', async () => {
    simularFetch(
      respuesta(401, { codigo: 'NO_AUTENTICADO', mensaje: 'Usuario o contraseña incorrectos.' }),
    );
    renderizar();
    await ingresar('oficial.bim11', 'mala');

    expect(await screen.findByRole('alert')).toHaveTextContent('Usuario o contraseña incorrectos.');
    expect(screen.queryByText('Bandeja de solicitudes')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ingresar' })).toBeEnabled();
  });

  it('valida los campos vacíos sin llamar a la API', async () => {
    const fetchSimulado = simularFetch();
    renderizar();
    await userEvent.setup().click(screen.getByRole('button', { name: 'Ingresar' }));

    expect(screen.getByText('Ingrese su usuario.')).toBeInTheDocument();
    expect(screen.getByText('Ingrese su contraseña.')).toBeInTheDocument();
    expect(fetchSimulado).not.toHaveBeenCalled();
  });

  it('desactiva el botón mientras espera la respuesta', async () => {
    let resolver: (r: Response) => void = () => undefined;
    globalThis.fetch = jest.fn(
      () => new Promise<Response>((r) => (resolver = r)),
    ) as unknown as typeof fetch;
    renderizar();
    await ingresar('oficial.bim11', 'secreta');

    expect(screen.getByRole('button', { name: 'Ingresando…' })).toBeDisabled();
    resolver(respuesta(200, token()));
    await waitFor(() => expect(screen.getByText('Bandeja de solicitudes')).toBeInTheDocument());
  });
});
