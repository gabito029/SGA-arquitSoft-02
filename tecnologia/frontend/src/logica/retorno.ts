// Ruta de retorno ligada a la sesión (T099).
//
// Solo se guarda cuando la sesión vence (401) mientras el usuario estaba en una página: así, al
// volver a entrar, retoma donde estaba. La ruta lleva el id de ese usuario y vive en
// sessionStorage (la misma pestaña). Al cerrar sesión se borra. Al iniciar sesión se usa solo si
// es del mismo usuario; en cualquier otro caso se va a la bandeja.

export const CLAVE_RETORNO = 'sga.retorno';
export const RUTA_BANDEJA = '/bandeja';

interface Retorno {
  ruta: string;
  usuarioId: string;
}

/** Solo rutas internas de la aplicación (evita redirecciones abiertas y la propia de ingreso). */
function esRutaInterna(ruta: string): boolean {
  return ruta.startsWith('/') && !ruta.startsWith('//') && !ruta.startsWith('/ingresar');
}

export function guardarRetorno(ruta: string, usuarioId: string): void {
  if (!esRutaInterna(ruta)) return;
  try {
    sessionStorage.setItem(CLAVE_RETORNO, JSON.stringify({ ruta, usuarioId } satisfies Retorno));
  } catch {
    // Sin almacenamiento disponible: simplemente no hay retorno.
  }
}

export function borrarRetorno(): void {
  try {
    sessionStorage.removeItem(CLAVE_RETORNO);
  } catch {
    // Nada que borrar.
  }
}

function leerRetorno(): Retorno | null {
  try {
    const texto = sessionStorage.getItem(CLAVE_RETORNO);
    if (!texto) return null;
    const datos = JSON.parse(texto) as Partial<Retorno>;
    return typeof datos.ruta === 'string' && typeof datos.usuarioId === 'string'
      ? (datos as Retorno)
      : null;
  } catch {
    return null;
  }
}

/** Destino al iniciar sesión: la ruta de retorno si es de este usuario; si no, la bandeja. */
export function destinoTrasIngreso(usuarioId: string): string {
  const retorno = leerRetorno();
  borrarRetorno(); // se usa una sola vez
  return retorno && retorno.usuarioId === usuarioId && esRutaInterna(retorno.ruta)
    ? retorno.ruta
    : RUTA_BANDEJA;
}
