// Pantalla de inicio de sesión (HU01, RF01). Tras entrar va a la bandeja, salvo que la sesión del
// mismo usuario haya vencido en esta pestaña: entonces retoma donde estaba (T099). Pantalla
// institucional y limpia (T109), con un escudo genérico: no usa logos ni escudos oficiales.
import { LogIn, Shield } from 'lucide-react';
import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { Token } from '../api/tipos';
import { useSesion } from '../auth/SesionContexto';
import { Campo, Formulario } from '../componentes/Formulario';
import { MENSAJE_GENERICO } from '../logica/mensajes';
import { destinoTrasIngreso, RUTA_BANDEJA } from '../logica/retorno';

export { RUTA_BANDEJA };

interface Errores {
  usuario?: string;
  contrasena?: string;
}

export function InicioSesion() {
  const { autenticado, guardarSesion } = useSesion();
  // Destino decidido al ingresar; el <Navigate> de abajo lo usa en cuanto hay sesión.
  const [destino, setDestino] = useState<string | null>(null);

  const [usuario, setUsuario] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [errores, setErrores] = useState<Errores>({});
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (autenticado) {
    return <Navigate to={destino ?? RUTA_BANDEJA} replace />;
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
      setDestino(destinoTrasIngreso(respuesta.usuario.id));
      guardarSesion(respuesta);
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
      setEnviando(false);
    }
  }

  return (
    <main className="ingreso">
      <div className="ingreso__panel">
        <div className="ingreso__identidad">
          <span className="ingreso__emblema">
            <Shield size={34} strokeWidth={1.5} />
          </span>
          <h1>SGA</h1>
          <p>Sistema de Gestión de Almacén con Firma Digital</p>
        </div>
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
          <button type="submit">
            <LogIn size={18} />
            {enviando ? 'Ingresando…' : 'Ingresar'}
          </button>
        </Formulario>
        <p className="ingreso__pie">Proyecto académico - IS488 UNSCH</p>
      </div>
    </main>
  );
}
