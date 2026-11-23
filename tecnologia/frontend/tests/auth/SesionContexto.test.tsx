// Contexto de sesión: guardar, recuperar, cerrar y cierre automático ante un 401.
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api, EVENTO_SESION_EXPIRADA } from '../../src/api/cliente';
import { CLAVE_ALMACENAMIENTO, SesionProveedor, useSesion } from '../../src/auth/SesionContexto';
import { respuesta, simularFetch, token } from '../apoyo/respuestas';

function Sonda() {
  const { autenticado, usuario, guardarSesion, cerrarSesion } = useSesion();
  return (
    <div>
      <p>{autenticado ? `Sesión de ${usuario?.usuario}` : 'Sin sesión'}</p>
      <button onClick={() => guardarSesion(token())}>Entrar</button>
      <button onClick={cerrarSesion}>Salir</button>
    </div>
  );
}

function renderizar() {
  return render(
    <SesionProveedor>
      <Sonda />
    </SesionProveedor>,
  );
}

afterEach(() => sessionStorage.clear());

describe('SesionContexto', () => {
  it('guarda la sesión en sessionStorage y la usa en las peticiones', async () => {
    renderizar();
    expect(screen.getByText('Sin sesión')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));
    expect(screen.getByText('Sesión de oficial.bim11')).toBeInTheDocument();
    expect(JSON.parse(sessionStorage.getItem(CLAVE_ALMACENAMIENTO) ?? '{}').token).toBe(
      'token-de-prueba',
    );

    const fetchSimulado = simularFetch(respuesta(200, {}));
    await api.get('/auth/me');
    expect(fetchSimulado.mock.calls[0][1].headers.Authorization).toBe('Bearer token-de-prueba');
  });

  it('recupera la sesión guardada al recargar', () => {
    sessionStorage.setItem(
      CLAVE_ALMACENAMIENTO,
      JSON.stringify({ token: 'guardado', usuario: token().usuario }),
    );
    renderizar();
    expect(screen.getByText('Sesión de oficial.bim11')).toBeInTheDocument();
  });

  it('ignora una sesión guardada dañada', () => {
    sessionStorage.setItem(CLAVE_ALMACENAMIENTO, '{no es json');
    renderizar();
    expect(screen.getByText('Sin sesión')).toBeInTheDocument();
  });

  it('cerrar sesión borra los datos', async () => {
    renderizar();
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));
    await userEvent.click(screen.getByRole('button', { name: 'Salir' }));
    expect(screen.getByText('Sin sesión')).toBeInTheDocument();
    expect(sessionStorage.getItem(CLAVE_ALMACENAMIENTO)).toBeNull();
  });

  it('el aviso de sesión expirada del cliente cierra la sesión', async () => {
    renderizar();
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));
    act(() => {
      window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA));
    });
    expect(screen.getByText('Sin sesión')).toBeInTheDocument();
  });

  it('useSesion fuera del proveedor lanza un error claro', () => {
    const consola = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Sonda />)).toThrow('useSesion debe usarse dentro de <SesionProveedor>');
    consola.mockRestore();
  });
});
