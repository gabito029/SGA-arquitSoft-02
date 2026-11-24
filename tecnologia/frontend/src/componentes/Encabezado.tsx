import { NavLink } from 'react-router-dom';
import { useSesion } from '../auth/SesionContexto';
import { ETIQUETAS_ROL } from '../logica/historial';
import { identificacion, menuPorRol } from '../logica/navegacion';

/**
 * Cabecera (T102): quién está conectado (sin repetir la unidad), su rol, el menú según el rol
 * (Bandeja para todos, Nueva solicitud para el oficial de logística y Stock para el almacén) y
 * cerrar sesión.
 */
export function Encabezado() {
  const { usuario, cerrarSesion } = useSesion();
  if (!usuario) return null;
  return (
    <header className="encabezado">
      <strong className="encabezado__marca">SGA</strong>
      <nav aria-label="Menú principal" className="encabezado__menu">
        <ul>
          {menuPorRol(usuario.rol).map((opcion) => (
            <li key={opcion.ruta}>
              <NavLink to={opcion.ruta} end>
                {opcion.etiqueta}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <span className="encabezado__usuario">
        {identificacion(usuario)}
        <small>{ETIQUETAS_ROL[usuario.rol]}</small>
      </span>
      <button type="button" className="boton--secundario" onClick={cerrarSesion}>
        Cerrar sesión
      </button>
    </header>
  );
}
