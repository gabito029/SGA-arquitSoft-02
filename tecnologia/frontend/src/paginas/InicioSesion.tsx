// Pantalla de inicio de sesión (HU01, RF01). Tras entrar, vuelve a la página pedida o a la bandeja.
import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { Token } from '../api/tipos';
import { useSesion } from '../auth/SesionContexto';
import { Campo, Formulario } from '../componentes/Formulario';
import { MENSAJE_GENERICO } from '../logica/mensajes';

export const RUTA_BANDEJA = '/bandeja';

interface Errores {
  usuario?: string;
  contrasena?: string;
}

export function InicioSesion() {
  const { autenticado, guardarSesion } = useSesion();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? RUTA_BANDEJA;

  const [usuario, setUsuario] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [errores, setErrores] = useState<Errores>({});
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (autenticado) {
    return <Navigate to={destino} replace />;
  }

  async function ingresar() {
    const nuevos: Errores = {};
    if (!usuario.trim()) nuevos.usuario = 'Ingrese su usuario.';
    if (!contrasena) nuevos.contrasena = 'Ingrese su contraseña.';
    setErrores(nuevos);
    setError(null);
    if (Object.keys(nuevos).length > 0) return;

    setEnviando(true);
    try {
      const respuesta = await api.post<Token>('/auth/login', {
        usuario: usuario.trim(),
        contrasena,
      });
      guardarSesion(respuesta);
      navegar(destino, { replace: true });
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
      setEnviando(false);
    }
  }

  return (
    <main className="contenedor contenedor--angosto">
      <h1>SGA — Gestión de Almacén</h1>
      <Formulario titulo="Iniciar sesión" enviando={enviando} error={error} onEnviar={ingresar}>
        <Campo id="usuario" etiqueta="Usuario" error={errores.usuario}>
          <input
            id="usuario"
            name="usuario"
            autoComplete="username"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            aria-invalid={Boolean(errores.usuario)}
          />
        </Campo>
        <Campo id="contrasena" etiqueta="Contraseña" error={errores.contrasena}>
          <input
            id="contrasena"
            name="contrasena"
            type="password"
            autoComplete="current-password"
            value={contrasena}
            onChange={(e) => setContrasena(e.target.value)}
            aria-invalid={Boolean(errores.contrasena)}
          />
        </Campo>
        <button type="submit">{enviando ? 'Ingresando…' : 'Ingresar'}</button>
      </Formulario>
    </main>
  );
}
