// Detalle de la solicitud: datos, ítems, firmas registradas y las acciones que la API permite al
// usuario (FR-029): Firmar y Rechazar (US2) y Despachar (US3). El acta, la verificación, la línea
// de tiempo y la anulación se agregan en las historias siguientes.
import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { Firma, Requerimiento } from '../api/tipos';
import { Cargando } from '../componentes/Cargando';
import { DialogoMotivo } from '../componentes/DialogoMotivo';
import { FormularioDespacho } from '../componentes/FormularioDespacho';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { Mensaje } from '../componentes/Mensaje';
import { decisionAprobar, decisionRechazar, puede } from '../logica/acciones';
import { ETIQUETAS_NIVEL, etiquetaEstado } from '../logica/estados';
import { MENSAJE_GENERICO } from '../logica/mensajes';

function textoError(e: unknown): string {
  return e instanceof ErrorApi ? e.message : MENSAJE_GENERICO;
}

function fecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' });
}

function ListaFirmas({ firmas }: { firmas: Firma[] }) {
  if (firmas.length === 0) return null;
  return (
    <section aria-labelledby="titulo-firmas">
      <h3 id="titulo-firmas">Firmas</h3>
      <ul className="lista">
        {firmas.map((f) => (
          <li key={f.id} className="lista__fila">
            <span>{ETIQUETAS_NIVEL[f.nivel]}</span>
            <span>
              {f.decision === 'APROBAR' ? 'Aprobó' : 'Rechazó'}: {f.firmante} ({f.organo.codigo})
            </span>
            <time dateTime={f.firmado_en}>{fecha(f.firmado_en)}</time>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function DetalleSolicitud() {
  const { id } = useParams<{ id: string }>();
  const [req, setReq] = useState<Requerimiento | null>(null);
  const [firmas, setFirmas] = useState<Firma[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [rechazando, setRechazando] = useState(false);

  const cargar = useCallback(async () => {
    const [detalle, registradas] = await Promise.all([
      api.get<Requerimiento>(`/requerimientos/${id}`),
      api.get<Firma[]>(`/requerimientos/${id}/firmas`),
    ]);
    setReq(detalle);
    setFirmas(registradas);
  }, [id]);

  useEffect(() => {
    let vigente = true;
    cargar().catch((e: unknown) => {
      if (vigente) setError(textoError(e));
    });
    return () => {
      vigente = false;
    };
  }, [cargar]);

  /** Ejecuta una acción, muestra el resultado y recarga el detalle. */
  async function ejecutar(accion: () => Promise<Requerimiento>, mensaje: (r: Requerimiento) => string) {
    setEnviando(true);
    setErrorAccion(null);
    setExito(null);
    try {
      const actualizado = await accion();
      setRechazando(false);
      setExito(mensaje(actualizado));
      await cargar();
    } catch (e: unknown) {
      setErrorAccion(textoError(e));
      // Si otro usuario cambió la solicitud, se muestra su estado real.
      if (e instanceof ErrorApi && e.estado === 409) await cargar().catch(() => undefined);
    } finally {
      setEnviando(false);
    }
  }

  function firmar() {
    void ejecutar(
      () => api.post<Requerimiento>(`/requerimientos/${id}/firmas`, decisionAprobar()),
      (r) => `Firmó la solicitud. Ahora está: ${etiquetaEstado(r.estado)}.`,
    );
  }

  function despachar(cuerpo: { items: { item_id: string; cantidad: number }[] }) {
    void ejecutar(
      () => api.post<Requerimiento>(`/requerimientos/${id}/despacho`, cuerpo),
      () => 'Despacho registrado. La solicitud está en tránsito.',
    );
  }

  function rechazar(motivo: string) {
    void ejecutar(
      () => api.post<Requerimiento>(`/requerimientos/${id}/firmas`, decisionRechazar(motivo)),
      () => 'Rechazó la solicitud.',
    );
  }

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
                {i.cantidad_despachada != null ? <span>Despachado: {i.cantidad_despachada}</span> : null}
              </li>
            ))}
          </ul>

          {exito ? <Mensaje tipo="exito">{exito}</Mensaje> : null}
          {errorAccion ? <Mensaje tipo="error">{errorAccion}</Mensaje> : null}
          {enviando ? <Cargando /> : null}

          {puede(req, 'FIRMAR') || puede(req, 'RECHAZAR') ? (
            <div className="formulario__acciones">
              {puede(req, 'FIRMAR') ? (
                <button type="button" className="boton" disabled={enviando} onClick={firmar}>
                  Firmar
                </button>
              ) : null}
              {puede(req, 'RECHAZAR') ? (
                <button
                  type="button"
                  className="boton--secundario"
                  disabled={enviando}
                  onClick={() => setRechazando(true)}
                >
                  Rechazar
                </button>
              ) : null}
            </div>
          ) : null}
          {rechazando ? (
            <DialogoMotivo
              titulo="Rechazar la solicitud"
              confirmar="Confirmar rechazo"
              enviando={enviando}
              onConfirmar={rechazar}
              onCancelar={() => setRechazando(false)}
            />
          ) : null}

          {puede(req, 'DESPACHAR') ? (
            <FormularioDespacho items={req.items} enviando={enviando} onDespachar={despachar} />
          ) : null}

          <ListaFirmas firmas={firmas} />
        </article>
      ) : null}
    </main>
  );
}
