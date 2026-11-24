// Raíz de la interfaz: sesión, rutas y encabezado. Cada ruta protegida exige sesión y, si
// corresponde, el rol; el backend vuelve a validar rol y órgano en cada petición.
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom';
import type { ReactNode } from 'react';
import type { Rol } from './api/tipos';
import { RUTA_INGRESO, RutaProtegida } from './auth/RutaProtegida';
import { SesionProveedor, useSesion } from './auth/SesionContexto';
import { Bandeja } from './paginas/Bandeja';
import { DetalleSolicitud } from './paginas/DetalleSolicitud';
import { InicioSesion, RUTA_BANDEJA } from './paginas/InicioSesion';
import { NuevaSolicitud } from './paginas/NuevaSolicitud';
import { Stock } from './paginas/Stock';

function Encabezado() {
  const { usuario, cerrarSesion } = useSesion();
  if (!usuario) return null;
  return (
    <header className="encabezado">
      <strong>SGA</strong>
      <span>
        {usuario.nombre_completo} · {usuario.organo.codigo}
      </span>
      {ROLES_ALMACEN.includes(usuario.rol) ? <Link to="/stock">Stock</Link> : null}
      <button type="button" className="boton--secundario" onClick={cerrarSesion}>
        Cerrar sesión
      </button>
    </header>
  );
}

const ROLES_ALMACEN: Rol[] = ['JEFE_ALMACEN', 'ALMACENERO'];

function Protegida({ children, soloOficial = false }: { children: ReactNode; soloOficial?: boolean }) {
  return (
    <RutaProtegida roles={soloOficial ? ['OFICIAL_LOGISTICA'] : undefined}>{children}</RutaProtegida>
  );
}

export function Rutas() {
  return (
    <>
      <Encabezado />
      <Routes>
        <Route path={RUTA_INGRESO} element={<InicioSesion />} />
        <Route
          path={RUTA_BANDEJA}
          element={
            <Protegida>
              <Bandeja />
            </Protegida>
          }
        />
        <Route
          path="/solicitudes/nueva"
          element={
            <Protegida soloOficial>
              <NuevaSolicitud />
            </Protegida>
          }
        />
        <Route
          path="/solicitudes/:id"
          element={
            <Protegida>
              <DetalleSolicitud />
            </Protegida>
          }
        />
        <Route
          path="/stock"
          element={
            <RutaProtegida roles={ROLES_ALMACEN}>
              <Stock />
            </RutaProtegida>
          }
        />
        <Route path="*" element={<Navigate to={RUTA_BANDEJA} replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <SesionProveedor>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Rutas />
      </BrowserRouter>
    </SesionProveedor>
  );
}
