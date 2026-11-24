// Bandeja de solicitudes (T063): lista paginada de lo que el usuario ve según su rol y órgano
// (la API aplica data-model.md §7), con filtro por estado, etiquetas de estado y los estados de
// carga y de lista vacía. Es una tabla con encabezados (T101) que en celular se muestra como
// tarjetas, con la etiqueta de cada dato.
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { EstadoRequerimiento, PaginaRequerimientos } from '../api/tipos';
import { useSesion } from '../auth/SesionContexto';
import { Cargando } from '../componentes/Cargando';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { Mensaje } from '../componentes/Mensaje';
import { accionPendiente } from '../logica/acciones';
import { estadosFiltrables, etiquetaEstado } from '../logica/estados';
import { fechaCorta } from '../logica/formato';
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
        <table className="tabla tabla--bandeja">
          <caption className="solo-lectores">
            Solicitudes visibles para su rol, de la más reciente a la más antigua
          </caption>
          <thead>
            <tr>
              <th scope="col">Código</th>
              <th scope="col">Categoría</th>
              <th scope="col">Unidad</th>
              <th scope="col">Fecha</th>
              <th scope="col">Estado</th>
              <th scope="col">Acción pendiente</th>
            </tr>
          </thead>
          <tbody>
            {datos.items.map((r) => {
              const pendiente = accionPendiente(r.acciones_disponibles);
              return (
                <tr key={r.id}>
                  <td data-etiqueta="Código">
                    <Link to={`/solicitudes/${r.id}`}>{r.codigo}</Link>
                  </td>
                  <td data-etiqueta="Categoría">
                    {r.categoria === 'INTENDENCIA' ? 'Intendencia' : 'Material de guerra'}
                  </td>
                  <td data-etiqueta="Unidad">{r.unidad.codigo}</td>
                  <td data-etiqueta="Fecha">
                    <time dateTime={r.creado_en}>{fechaCorta(r.creado_en)}</time>
                  </td>
                  <td data-etiqueta="Estado">
                    <EstadoEtiqueta estado={r.estado} />
                  </td>
                  <td data-etiqueta="Acción pendiente">
                    {pendiente ? <span className="pendiente">{pendiente}</span> : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
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
