// Detalle mínimo de la US1: datos, ítems y estado de la solicitud. La línea de tiempo y los
// botones Firmar/Rechazar llegan con el detalle completo (US2 y US5).
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { Requerimiento } from '../api/tipos';
import { Cargando } from '../componentes/Cargando';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { Mensaje } from '../componentes/Mensaje';
import { MENSAJE_GENERICO } from '../logica/mensajes';

export function DetalleSolicitud() {
  const { id } = useParams<{ id: string }>();
  const [req, setReq] = useState<Requerimiento | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    api
      .get<Requerimiento>(`/requerimientos/${id}`)
      .then((r) => {
        if (vigente) setReq(r);
      })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
      });
    return () => {
      vigente = false;
    };
  }, [id]);

  return (
    <main className="contenedor">
      <p>
        <Link to="/bandeja">← Volver a la bandeja</Link>
      </p>
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      {!req && !error ? <Cargando /> : null}
      {req ? (
        <article>
          <h2>
            {req.codigo} <EstadoEtiqueta estado={req.estado} />
          </h2>
          <p>
            Unidad: {req.unidad.nombre} ({req.unidad.codigo})
            {req.almacen ? ` · Almacén: ${req.almacen.nombre}` : ''}
            {req.monto_total ? ` · Monto: S/ ${req.monto_total}` : ''}
          </p>
          <ul className="lista">
            {req.items.map((i) => (
              <li key={i.item.id} className="lista__fila">
                <span>
                  {i.item.codigo} — {i.item.nombre}
                </span>
                <strong>
                  {i.cantidad_solicitada} {i.item.unidad_medida}
                </strong>
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </main>
  );
}
