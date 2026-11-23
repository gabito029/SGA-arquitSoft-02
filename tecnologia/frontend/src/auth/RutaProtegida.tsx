// Ruta que exige sesión y, opcionalmente, uno de los roles indicados. El backend vuelve a
// validar el rol y el órgano en cada petición; esto solo evita mostrar lo que no corresponde.
import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import type { Rol } from '../api/tipos';
import { Mensaje } from '../componentes/Mensaje';
import { useSesion } from './SesionContexto';

export const RUTA_INGRESO = '/ingresar';

interface Props {
  roles?: readonly Rol[];
  children: ReactNode;
}

export function RutaProtegida({ roles, children }: Props) {
  const { usuario } = useSesion();
  const ubicacion = useLocation();

  if (!usuario) {
    return <Navigate to={RUTA_INGRESO} replace state={{ desde: ubicacion.pathname }} />;
  }
  if (roles && !roles.includes(usuario.rol)) {
    return <Mensaje tipo="error">Su rol no permite ver esta página.</Mensaje>;
  }
  return <>{children}</>;
}
