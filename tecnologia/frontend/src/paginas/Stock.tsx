// Stock del almacén del usuario (T072): tabla paginada para JEFE_ALMACEN y ALMACENERO.
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { Stock as FilaStock } from '../api/tipos';
import { Cargando } from '../componentes/Cargando';
import { Mensaje } from '../componentes/Mensaje';
import { MENSAJE_GENERICO } from '../logica/mensajes';

interface PaginaStock {
  items: FilaStock[];
  total: number;
  page: number;
  size: number;
}

const TAMANO_PAGINA = 20;

export function Stock() {
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState<PaginaStock | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    setError(null);
    api
      .get<PaginaStock>('/inventario/stock', { page: pagina, size: TAMANO_PAGINA })
      .then((r) => {
        if (vigente) setDatos(r);
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
      <p>
        <Link to="/bandeja">← Volver a la bandeja</Link>
      </p>
      <h2>Stock del almacén</h2>
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      {!datos && !error ? <Cargando /> : null}
      {datos && datos.items.length === 0 ? <p>El almacén no tiene stock registrado.</p> : null}
      {datos && datos.items.length > 0 ? (
        <table className="tabla">
          <thead>
            <tr>
              <th scope="col">Código</th>
              <th scope="col">Ítem</th>
              <th scope="col">Cantidad</th>
            </tr>
          </thead>
          <tbody>
            {datos.items.map((s) => (
              <tr key={s.item.id}>
                <td>{s.item.codigo}</td>
                <td>{s.item.nombre}</td>
                <td>
                  {s.cantidad} {s.item.unidad_medida}
                </td>
              </tr>
            ))}
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
