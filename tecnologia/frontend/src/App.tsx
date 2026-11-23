// Raíz de la interfaz. Las rutas (/ingresar, /bandeja, /solicitudes/...) se configuran en T053
// (US1); por ahora solo se monta el contexto de sesión.
import { SesionProveedor } from './auth/SesionContexto';

export default function App() {
  return (
    <SesionProveedor>
      <main className="contenedor">
        <h1>SGA — Gestión de Almacén</h1>
        <p>Incremento 001 en construcción.</p>
      </main>
    </SesionProveedor>
  );
}
