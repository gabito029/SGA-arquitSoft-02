// T041: rutas protegidas por sesión y rol.
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RutaProtegida, RUTA_INGRESO } from '../../src/auth/RutaProtegida';
import { CLAVE_ALMACENAMIENTO, SesionProveedor } from '../../src/auth/SesionContexto';
import { token } from '../apoyo/respuestas';

function renderizar(roles?: Parameters<typeof RutaProtegida>[0]['roles']) {
  return render(
    <SesionProveedor>
      <MemoryRouter initialEntries={['/bandeja']}>
        <Routes>
          <Route path={RUTA_INGRESO} element={<p>Pantalla de inicio de sesión</p>} />
          <Route
            path="/bandeja"
            element={
              <RutaProtegida roles={roles}>
                <p>Contenido protegido</p>
              </RutaProtegida>
            }
          />
        </Routes>
      </MemoryRouter>
    </SesionProveedor>,
  );
}

afterEach(() => sessionStorage.clear());

describe('RutaProtegida', () => {
  it('sin sesión redirige al inicio de sesión', () => {
    renderizar();
    expect(screen.getByText('Pantalla de inicio de sesión')).toBeInTheDocument();
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument();
  });

  it('con un rol no permitido no muestra la página', () => {
    sessionStorage.setItem(CLAVE_ALMACENAMIENTO, JSON.stringify({ token: 't', usuario: token().usuario }));
    renderizar(['ALMACENERO', 'JEFE_ALMACEN']);
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Su rol no permite ver esta página.');
  });

  it('con un rol permitido sí la muestra', () => {
    sessionStorage.setItem(CLAVE_ALMACENAMIENTO, JSON.stringify({ token: 't', usuario: token().usuario }));
    renderizar(['OFICIAL_LOGISTICA']);
    expect(screen.getByText('Contenido protegido')).toBeInTheDocument();
  });

  it('sin restricción de roles, basta con tener sesión', () => {
    sessionStorage.setItem(CLAVE_ALMACENAMIENTO, JSON.stringify({ token: 't', usuario: token().usuario }));
    renderizar();
    expect(screen.getByText('Contenido protegido')).toBeInTheDocument();
  });
});
