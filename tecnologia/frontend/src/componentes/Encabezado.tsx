import { FilePlus, Inbox, LogOut, Shield, Warehouse, type LucideIcon } from 'lucide-react';
import { Link, NavLink } from 'react-router-dom';
import { useSesion } from '../auth/SesionContexto';
import { ETIQUETAS_ROL } from '../logica/historial';
import { identificacion, menuPorRol } from '../logica/navegacion';

const ICONOS_MENU: Record<string, LucideIcon> = {
  '/bandeja': Inbox,
  '/solicitudes/nueva': FilePlus,
  '/stock': Warehouse,
};

/**
 * Cabecera (T102, T109): marca del sistema, quién está conectado (sin repetir la unidad), su rol,
 * el menú según el rol (Bandeja para todos, Nueva solicitud para el oficial de logística y Stock
 * para el almacén) y cerrar sesión.
 */
export function Encabezado() {
  const { usuario, cerrarSesion } = useSesion();
  if (!usuario) return null;
  return (
    <header className="encabezado">
      <Link to="/bandeja" className="encabezado__marca" aria-label="SGA: ir a la bandeja">
        <Shield size={22} />
        <strong>SGA</strong>
        <small>Gestión de Almacén</small>
      </Link>
      <nav aria-label="Menú principal" className="encabezado__menu">
        <ul>
          {menuPorRol(usuario.rol).map((opcion) => {
            const Icono = ICONOS_MENU[opcion.ruta] ?? Inbox;
            return (
              <li key={opcion.ruta}>
                <NavLink to={opcion.ruta} end>
                  <Icono size={16} />
                  {opcion.etiqueta}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>
      <span className="encabezado__usuario">
        {identificacion(usuario)}
        <small>{ETIQUETAS_ROL[usuario.rol]}</small>
      </span>
      <button type="button" className="boton--secundario boton--salir" onClick={cerrarSesion}>
        <LogOut size={16} />
        Cerrar sesión
      </button>
    </header>
  );
}
