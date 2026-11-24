// Raíz de la interfaz: sesión, rutas y encabezado. Cada ruta protegida exige sesión y, si
// corresponde, el rol; el backend vuelve a validar rol y órgano en cada petición.
import { LucideProvider } from 'lucide-react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import type { ReactNode } from 'react';
import { RUTA_INGRESO, RutaProtegida } from './auth/RutaProtegida';
import { SesionProveedor } from './auth/SesionContexto';
import { Encabezado } from './componentes/Encabezado';
import { ROLES_ALMACEN } from './logica/navegacion';
import { Bandeja } from './paginas/Bandeja';
import { DetalleSolicitud } from './paginas/DetalleSolicitud';
import { InicioSesion, RUTA_BANDEJA } from './paginas/InicioSesion';
import { NuevaSolicitud } from './paginas/NuevaSolicitud';
import { Stock } from './paginas/Stock';

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
      {/* Íconos de lucide-react (T107): mismo trazo y tamaño en toda la interfaz. */}
      <LucideProvider size={18} strokeWidth={1.75} className="icono">
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Rutas />
        </BrowserRouter>
      </LucideProvider>
    </SesionProveedor>
  );
}
