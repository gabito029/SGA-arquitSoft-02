// Contexto de sesión: token y usuario en memoria y en sessionStorage (se borra al cerrar la
// pestaña). La API no guarda sesión en el servidor (ADR-006).
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { EVENTO_SESION_EXPIRADA, fijarToken } from '../api/cliente';
import type { Token, Usuario } from '../api/tipos';
import { borrarRetorno, guardarRetorno } from '../logica/retorno';

export const CLAVE_ALMACENAMIENTO = 'sga.sesion';

interface DatosSesion {
  token: string;
  usuario: Usuario;
}

export interface ValorSesion {
  token: string | null;
  usuario: Usuario | null;
  autenticado: boolean;
  guardarSesion: (respuesta: Token) => void;
  cerrarSesion: () => void;
}

const SesionContexto = createContext<ValorSesion | null>(null);

function leerAlmacenada(): DatosSesion | null {
  try {
    const texto = sessionStorage.getItem(CLAVE_ALMACENAMIENTO);
    if (!texto) return null;
    const datos = JSON.parse(texto) as Partial<DatosSesion>;
    return datos.token && datos.usuario ? (datos as DatosSesion) : null;
  } catch {
    return null;
  }
}

function escribirAlmacenada(datos: DatosSesion | null): void {
  try {
    if (datos) {
      sessionStorage.setItem(CLAVE_ALMACENAMIENTO, JSON.stringify(datos));
    } else {
      sessionStorage.removeItem(CLAVE_ALMACENAMIENTO);
    }
  } catch {
    // Sin almacenamiento (modo privado o bloqueado): la sesión vive solo en memoria.
  }
}

export function SesionProveedor({ children }: { children: ReactNode }) {
  const [datos, setDatos] = useState<DatosSesion | null>(() => {
    const almacenada = leerAlmacenada();
    fijarToken(almacenada?.token ?? null);
    return almacenada;
  });

  const guardarSesion = useCallback((respuesta: Token) => {
    const nuevos = { token: respuesta.access_token, usuario: respuesta.usuario };
    fijarToken(nuevos.token);
    escribirAlmacenada(nuevos);
    setDatos(nuevos);
  }, []);

  const limpiar = useCallback(() => {
    fijarToken(null);
    escribirAlmacenada(null);
    setDatos(null);
  }, []);

  /** Cierre explícito: no queda ninguna ruta de retorno para el próximo usuario (T099). */
  const cerrarSesion = useCallback(() => {
    borrarRetorno();
    limpiar();
  }, [limpiar]);

  // Si la sesión vence (401), se guarda dónde estaba este usuario para retomar al volver a entrar.
  const usuarioActual = useRef<Usuario | null>(datos?.usuario ?? null);
  usuarioActual.current = datos?.usuario ?? null;
  useEffect(() => {
    function alVencer() {
      const usuario = usuarioActual.current;
      if (usuario) guardarRetorno(window.location.pathname + window.location.search, usuario.id);
      limpiar();
    }
    window.addEventListener(EVENTO_SESION_EXPIRADA, alVencer);
    return () => window.removeEventListener(EVENTO_SESION_EXPIRADA, alVencer);
  }, [limpiar]);

  const valor = useMemo<ValorSesion>(
    () => ({
      token: datos?.token ?? null,
      usuario: datos?.usuario ?? null,
      autenticado: datos !== null,
      guardarSesion,
      cerrarSesion,
    }),
    [datos, guardarSesion, cerrarSesion],
  );

  return <SesionContexto.Provider value={valor}>{children}</SesionContexto.Provider>;
}

export function useSesion(): ValorSesion {
  const valor = useContext(SesionContexto);
  if (!valor) {
    throw new Error('useSesion debe usarse dentro de <SesionProveedor>');
  }
  return valor;
}
