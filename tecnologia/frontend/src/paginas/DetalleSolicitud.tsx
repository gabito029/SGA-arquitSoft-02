// Detalle de la solicitud: datos, ítems, firmas registradas y las acciones que la API permite al
// usuario (FR-029): Firmar y Rechazar (US2), Despachar (US3), Firmar acta y Verificar (US4), la
// línea de tiempo (US5) y Anular (US6).
import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { EntradaHistorial, Firma, Requerimiento, Verificacion } from '../api/tipos';
import { Cargando } from '../componentes/Cargando';
import { DialogoMotivo } from '../componentes/DialogoMotivo';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { FormularioActa } from '../componentes/FormularioActa';
import { FormularioDespacho } from '../componentes/FormularioDespacho';
import { LineaTiempo } from '../componentes/LineaTiempo';
import { Mensaje } from '../componentes/Mensaje';
import { ResultadoVerificacion } from '../componentes/ResultadoVerificacion';
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

type CuerpoDespacho = { items: { item_id: string; cantidad: number }[] };
type CuerpoActa = { items: { item_id: string; cantidad_recibida: number; observacion?: string }[] };

export function DetalleSolicitud() {
  const { id } = useParams<{ id: string }>();
  const [req, setReq] = useState<Requerimiento | null>(null);
  const [firmas, setFirmas] = useState<Firma[]>([]);
  const [verificacion, setVerificacion] = useState<Verificacion | null>(null);
  const [historial, setHistorial] = useState<EntradaHistorial[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [rechazando, setRechazando] = useState(false);
  const [anulando, setAnulando] = useState(false);

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
  async function ejecutar<T>(accion: () => Promise<T>, mensaje: (r: T) => string) {
    setEnviando(true);
    setErrorAccion(null);
    setExito(null);
    setVerificacion(null);
    setHistorial(null);
    try {
      const resultado = await accion();
      setRechazando(false);
      setAnulando(false);
      setExito(mensaje(resultado));
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

  function rechazar(motivo: string) {
    void ejecutar(
      () => api.post<Requerimiento>(`/requerimientos/${id}/firmas`, decisionRechazar(motivo)),
      () => 'Rechazó la solicitud.',
    );
  }

  function anular(motivo: string) {
    void ejecutar(
      () => api.post<Requerimiento>(`/requerimientos/${id}/anular`, { motivo }),
      () => 'Anuló la solicitud. Queda registrada con su motivo en la línea de tiempo.',
    );
  }

  function despachar(cuerpo: CuerpoDespacho) {
    void ejecutar(
      () => api.post<Requerimiento>(`/requerimientos/${id}/despacho`, cuerpo),
      () => 'Despacho registrado. La solicitud está en tránsito.',
    );
  }

  function firmarActa(cuerpo: CuerpoActa) {
    void ejecutar(
      () => api.post<{ tiene_diferencias: boolean }>(`/requerimientos/${id}/acta`, cuerpo),
      (acta) =>
        acta.tiene_diferencias
          ? 'Acta firmada con diferencias registradas. La solicitud está recibida.'
          : 'Acta firmada. La solicitud está recibida.',
    );
  }

  async function verificar() {
    setEnviando(true);
    setErrorAccion(null);
    setExito(null);
    try {
      setVerificacion(await api.get<Verificacion>(`/requerimientos/${id}/verificacion`));
    } catch (e: unknown) {
      setErrorAccion(textoError(e));
    } finally {
      setEnviando(false);
    }
  }

  async function verHistorial() {
    if (historial) {
      setHistorial(null);
      return;
    }
    setErrorAccion(null);
    try {
      setHistorial(await api.get<EntradaHistorial[]>(`/requerimientos/${id}/historial`));
    } catch (e: unknown) {
      setErrorAccion(textoError(e));
    }
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
                {i.cantidad_recibida != null ? <span>Recibido: {i.cantidad_recibida}</span> : null}
                {i.observacion ? <span>Observación: {i.observacion}</span> : null}
              </li>
            ))}
          </ul>

          {exito ? <Mensaje tipo="exito">{exito}</Mensaje> : null}
          {errorAccion ? <Mensaje tipo="error">{errorAccion}</Mensaje> : null}
          {enviando ? <Cargando /> : null}

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
            {puede(req, 'ANULAR') ? (
              <button
                type="button"
                className="boton--secundario"
                disabled={enviando}
                onClick={() => setAnulando(true)}
              >
                Anular
              </button>
            ) : null}
            {firmas.length > 0 ? (
              <button
                type="button"
                className="boton--secundario"
                disabled={enviando}
                onClick={() => void verificar()}
              >
                Verificar
              </button>
            ) : null}
          </div>
          {rechazando ? (
            <DialogoMotivo
              titulo="Rechazar la solicitud"
              confirmar="Confirmar rechazo"
              enviando={enviando}
              onConfirmar={rechazar}
              onCancelar={() => setRechazando(false)}
            />
          ) : null}

          {anulando ? (
            <DialogoMotivo
              titulo="Anular la solicitud"
              confirmar="Confirmar anulación"
              enviando={enviando}
              onConfirmar={anular}
              onCancelar={() => setAnulando(false)}
            />
          ) : null}

          {puede(req, 'DESPACHAR') ? (
            <FormularioDespacho items={req.items} enviando={enviando} onDespachar={despachar} />
          ) : null}
          {puede(req, 'FIRMAR_ACTA') ? (
            <FormularioActa items={req.items} enviando={enviando} onFirmar={firmarActa} />
          ) : null}

          {verificacion ? <ResultadoVerificacion verificacion={verificacion} /> : null}
          <ListaFirmas firmas={firmas} />

          <section aria-labelledby="titulo-historial">
            <h3 id="titulo-historial">Línea de tiempo</h3>
            <button
              type="button"
              className="boton--secundario"
              aria-expanded={historial !== null}
              onClick={() => void verHistorial()}
            >
              {historial ? 'Ocultar línea de tiempo' : 'Ver línea de tiempo'}
            </button>
            {historial ? <LineaTiempo entradas={historial} /> : null}
          </section>
        </article>
      ) : null}
    </main>
  );
}
