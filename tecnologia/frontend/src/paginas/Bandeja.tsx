// Bandeja mínima de la US1: las solicitudes visibles para el usuario con su estado, paginadas.
// El filtro por estado y las acciones por rol llegan con la bandeja completa (US2, T066).
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { PaginaRequerimientos } from '../api/tipos';
import { useSesion } from '../auth/SesionContexto';
import { Cargando } from '../componentes/Cargando';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { Mensaje } from '../componentes/Mensaje';
import { MENSAJE_GENERICO } from '../logica/mensajes';

const TAMANO_PAGINA = 20;

export function Bandeja() {
  const { usuario } = useSesion();
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState<PaginaRequerimientos | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    setError(null);
    api
      .get<PaginaRequerimientos>('/requerimientos', { page: pagina, size: TAMANO_PAGINA })
      .then((respuesta) => {
        if (vigente) setDatos(respuesta);
      })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
      });
    return () => {
      vigente = false;
    };
  }, [pagina]);

  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / datos.size)) : 1;

  return (
    <main className="contenedor">
      <div className="barra">
        <h2>Bandeja de solicitudes</h2>
        {usuario?.rol === 'OFICIAL_LOGISTICA' ? (
          <Link className="boton" to="/solicitudes/nueva">
            Nueva solicitud
          </Link>
        ) : null}
      </div>
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      {!datos && !error ? <Cargando /> : null}
      {datos && datos.items.length === 0 ? <p>No hay solicitudes para mostrar.</p> : null}
      {datos && datos.items.length > 0 ? (
        <ul className="lista">
          {datos.items.map((r) => (
            <li key={r.id} className="lista__fila">
              <Link to={`/solicitudes/${r.id}`}>{r.codigo}</Link>
              <span>{r.categoria === 'INTENDENCIA' ? 'Intendencia' : 'Material de guerra'}</span>
              <span>{r.unidad.codigo}</span>
              <EstadoEtiqueta estado={r.estado} />
            </li>
          ))}
        </ul>
      ) : null}
      {datos && totalPaginas > 1 ? (
        <nav className="paginacion" aria-label="Paginación">
          <button type="button" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>
            Anterior
          </button>
          <span>
            Página {pagina} de {totalPaginas}
          </span>
          <button
            type="button"
            disabled={pagina >= totalPaginas}
            onClick={() => setPagina(pagina + 1)}
          >
            Siguiente
          </button>
        </nav>
      ) : null}
    </main>
  );
}
