// Bandeja de solicitudes (T063): lista paginada de lo que el usuario ve según su rol y órgano
// (la API aplica data-model.md §7), con filtro por estado, etiquetas de estado y los estados de
// carga y de lista vacía.
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { EstadoRequerimiento, PaginaRequerimientos } from '../api/tipos';
import { useSesion } from '../auth/SesionContexto';
import { Cargando } from '../componentes/Cargando';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { Mensaje } from '../componentes/Mensaje';
import { ETIQUETAS_ACCION } from '../logica/acciones';
import { estadosFiltrables, etiquetaEstado } from '../logica/estados';
import { MENSAJE_GENERICO } from '../logica/mensajes';

export const TAMANO_PAGINA = 20;

export function Bandeja() {
  const { usuario } = useSesion();
  const [pagina, setPagina] = useState(1);
  const [estado, setEstado] = useState<EstadoRequerimiento | ''>('');
  const [datos, setDatos] = useState<PaginaRequerimientos | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    setError(null);
    setCargando(true);
    api
      .get<PaginaRequerimientos>('/requerimientos', {
        page: pagina,
        size: TAMANO_PAGINA,
        estado: estado || undefined,
      })
      .then((respuesta) => {
        if (vigente) setDatos(respuesta);
      })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });
    return () => {
      vigente = false;
    };
  }, [pagina, estado]);

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
      <div className="campo">
        <label className="campo__etiqueta" htmlFor="filtro-estado">
          Estado
        </label>
        <select
          id="filtro-estado"
          value={estado}
          onChange={(e) => {
            setEstado(e.target.value as EstadoRequerimiento | '');
            setPagina(1);
          }}
        >
          <option value="">Todos</option>
          {estadosFiltrables(usuario?.rol).map((e) => (
            <option key={e} value={e}>
              {etiquetaEstado(e)}
            </option>
          ))}
        </select>
      </div>
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      {cargando ? <Cargando /> : null}
      {!cargando && datos && datos.items.length === 0 ? (
        <p>{estado ? 'No hay solicitudes en este estado.' : 'No hay solicitudes para mostrar.'}</p>
      ) : null}
      {datos && datos.items.length > 0 ? (
        <ul className="lista" aria-label="Solicitudes">
          {datos.items.map((r) => (
            <li key={r.id} className="lista__fila">
              <Link to={`/solicitudes/${r.id}`}>{r.codigo}</Link>
              <span>{r.categoria === 'INTENDENCIA' ? 'Intendencia' : 'Material de guerra'}</span>
              <span>{r.unidad.codigo}</span>
              <EstadoEtiqueta estado={r.estado} />
              {r.acciones_disponibles.length > 0 ? (
                <span className="pendiente">
                  Pendiente: {r.acciones_disponibles.map((a) => ETIQUETAS_ACCION[a]).join(', ')}
                </span>
              ) : null}
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
