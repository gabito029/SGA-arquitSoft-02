// Menú de la cabecera según el rol (T102). El backend vuelve a validar cada acceso.
import type { Rol, Usuario } from '../api/tipos';

export interface OpcionMenu {
  ruta: string;
  etiqueta: string;
}

export const ROLES_ALMACEN: readonly Rol[] = ['JEFE_ALMACEN', 'ALMACENERO'];

export function menuPorRol(rol: Rol): OpcionMenu[] {
  const opciones: OpcionMenu[] = [{ ruta: '/bandeja', etiqueta: 'Bandeja' }];
  if (rol === 'OFICIAL_LOGISTICA') {
    opciones.push({ ruta: '/solicitudes/nueva', etiqueta: 'Nueva solicitud' });
  }
  if (ROLES_ALMACEN.includes(rol)) {
    opciones.push({ ruta: '/stock', etiqueta: 'Stock' });
  }
  return opciones;
}

/**
 * Cómo se identifica al usuario en la cabecera, sin repetir el órgano: si el nombre ya lo
 * incluye ("Oficial de logística BIM-11"), no se agrega otra vez.
 */
export function identificacion(usuario: Usuario): string {
  const { nombre_completo: nombre, organo } = usuario;
  return nombre.includes(organo.codigo) ? nombre : `${nombre} · ${organo.codigo}`;
}
