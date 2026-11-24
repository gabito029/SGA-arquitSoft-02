// T102: cabecera sin la unidad repetida y con el menú según el rol; T099: cerrar sesión.
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { fijarToken } from '../../src/api/cliente';
import type { Rol, Usuario } from '../../src/api/tipos';
import { SesionProveedor } from '../../src/auth/SesionContexto';
import { Encabezado } from '../../src/componentes/Encabezado';
import { identificacion, menuPorRol } from '../../src/logica/navegacion';
import { CLAVE_RETORNO } from '../../src/logica/retorno';
import { token, USUARIO_OFICIAL } from '../apoyo/respuestas';

function usuario(rol: Rol, nombre: string, codigo: string): Usuario {
  return {
    ...USUARIO_OFICIAL,
    rol,
    nombre_completo: nombre,
    organo: { id: 'o', codigo, nombre: codigo },
  };
}

function renderizar(u: Usuario, ruta = '/bandeja') {
  sessionStorage.setItem('sga.sesion', JSON.stringify({ token: token(u).access_token, usuario: u }));
  return render(
    <SesionProveedor>
      <MemoryRouter
        initialEntries={[ruta]}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Encabezado />
      </MemoryRouter>
    </SesionProveedor>,
  );
}

afterEach(() => {
  sessionStorage.clear();
  fijarToken(null);
});

describe('menuPorRol', () => {
  it.each<[Rol, string[]]>([
    ['OFICIAL_LOGISTICA', ['Bandeja', 'Nueva solicitud']],
    ['JEFE_ALMACEN', ['Bandeja', 'Stock']],
    ['ALMACENERO', ['Bandeja', 'Stock']],
    ['COMANDANTE_UNIDAD', ['Bandeja']],
    ['JEFE_LOGISTICA_GU', ['Bandeja']],
    ['AUDITOR', ['Bandeja']],
  ])('%s → %j', (rol, esperado) => {
    expect(menuPorRol(rol).map((o) => o.etiqueta)).toEqual(esperado);
  });
});

describe('identificacion', () => {
  it('no repite el órgano si el nombre ya lo incluye', () => {
    expect(
      identificacion(usuario('OFICIAL_LOGISTICA', 'Oficial de logística BIM-11', 'BIM-11')),
    ).toBe('Oficial de logística BIM-11');
    expect(identificacion(usuario('AUDITOR', 'Auditor de la Inspectoría', 'IGE'))).toBe(
      'Auditor de la Inspectoría · IGE',
    );
  });
});

describe('Encabezado', () => {
  it('muestra el menú del oficial, marca la página actual y no repite la unidad', () => {
    renderizar(usuario('OFICIAL_LOGISTICA', 'Oficial de logística BIM-11', 'BIM-11'));
    const menu = screen.getByRole('navigation', { name: 'Menú principal' });
    expect(within(menu).getAllByRole('link').map((a) => a.textContent)).toEqual([
      'Bandeja',
      'Nueva solicitud',
    ]);
    expect(within(menu).getByRole('link', { name: 'Bandeja' })).toHaveAttribute(
      'aria-current',
      'page',
    );
    expect(screen.getByText('Oficial de logística BIM-11')).toBeInTheDocument();
    expect(screen.queryByText(/BIM-11 · BIM-11/)).not.toBeInTheDocument();
    expect(screen.getByText('Oficial de logística')).toBeInTheDocument(); // el rol
  });

  it('el almacenero ve Stock y no Nueva solicitud', () => {
    renderizar(usuario('ALMACENERO', 'Almacenero de Intendencia', 'SINTE'), '/stock');
    const menu = screen.getByRole('navigation', { name: 'Menú principal' });
    expect(within(menu).getByRole('link', { name: 'Stock' })).toHaveAttribute(
      'aria-current',
      'page',
    );
    expect(within(menu).queryByRole('link', { name: 'Nueva solicitud' })).not.toBeInTheDocument();
  });

  it('cerrar sesión borra la ruta de retorno guardada (T099)', async () => {
    renderizar(USUARIO_OFICIAL);
    sessionStorage.setItem(CLAVE_RETORNO, JSON.stringify({ ruta: '/stock', usuarioId: 'x' }));
    await userEvent.setup().click(screen.getByRole('button', { name: 'Cerrar sesión' }));
    expect(sessionStorage.getItem(CLAVE_RETORNO)).toBeNull();
    expect(sessionStorage.getItem('sga.sesion')).toBeNull();
  });

  it('sin sesión no muestra nada', () => {
    const { container } = render(
      <SesionProveedor>
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Encabezado />
        </MemoryRouter>
      </SesionProveedor>,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
