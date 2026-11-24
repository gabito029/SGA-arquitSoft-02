// Detalle de la solicitud: datos, ítems, firmas registradas y las acciones que la API permite al
// usuario (FR-029): Firmar y Rechazar (US2), Despachar (US3), Firmar acta y Verificar (US4), la
// línea de tiempo (US5) y Anular (US6). Firmar, Rechazar, Despachar y Firmar acta piden una
// confirmación dentro de la página, porque no se pueden deshacer (T100). Presentación (T111): las
// firmas se muestran como sellos (nivel, cargo, fecha, hora y huella abreviada) y la línea de
// tiempo como la secuencia del conducto regular.
import {
  ArrowLeft,
  Ban,
  Building2,
  CircleX,
  Clock,
  Coins,
  Feather,
  FileText,
  Package,
  ShieldCheck,
  Stamp,
  Warehouse,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import { obtenerDocumento } from '../api/documentos';
import { stockPorItem } from '../api/inventario';
import type {
  Documento,
  EntradaHistorial,
  Firma,
  Requerimiento,
  Verificacion,
} from '../api/tipos';
import { Cargando } from '../componentes/Cargando';
import { DialogoConfirmacion } from '../componentes/DialogoConfirmacion';
import { DialogoMotivo } from '../componentes/DialogoMotivo';
import { DocumentoOficial } from '../componentes/DocumentoOficial';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { FormularioActa } from '../componentes/FormularioActa';
import { FormularioDespacho } from '../componentes/FormularioDespacho';
import { LineaTiempo } from '../componentes/LineaTiempo';
import { Mensaje } from '../componentes/Mensaje';
import { ResultadoVerificacion } from '../componentes/ResultadoVerificacion';
import {
  ADVERTENCIA_FIRMA,
  ADVERTENCIA_RECHAZO,
  decisionAprobar,
  decisionRechazar,
  puede,
} from '../logica/acciones';
import { ETIQUETAS_NIVEL, etiquetaEstado } from '../logica/estados';
import { cantidadConUnidad, fechaHora, formatoSoles, huellaAbreviada } from '../logica/formato';
import { ETIQUETAS_ROL } from '../logica/historial';
import { MENSAJE_GENERICO } from '../logica/mensajes';

function textoError(e: unknown): string {
  return e instanceof ErrorApi ? e.message : MENSAJE_GENERICO;
}

/** Firmas registradas como sellos: nivel, decisión, firmante, cargo, fecha, hora y huella. */
function ListaFirmas({ firmas }: { firmas: Firma[] }) {
  if (firmas.length === 0) return null;
  return (
    <section className="seccion" aria-labelledby="titulo-firmas">
      <p className="antetitulo">Sellos de firma digital</p>
      <h3 id="titulo-firmas">
        <Stamp />
        Firmas
      </h3>
      <ul className="sellos">
        {firmas.map((f) => {
          const aprobo = f.decision === 'APROBAR';
          const { fecha, hora } = fechaHora(f.firmado_en);
          return (
            <li key={f.id} className={`sello sello--${aprobo ? 'aprobado' : 'rechazado'}`}>
              <p className="sello__cabecera">
                <Stamp size={16} />
                <span>{ETIQUETAS_NIVEL[f.nivel]}</span>
              </p>
              <p className="sello__firmante">
                {aprobo ? 'Aprobó' : 'Rechazó'}: {f.firmante}
              </p>
              <p className="sello__cargo">
                {ETIQUETAS_ROL[f.rol]} · {f.organo.codigo}
              </p>
              <dl className="sello__datos">
                <dt>Fecha</dt>
                <dd>
                  <time dateTime={f.firmado_en}>{fecha}</time>
                </dd>
                <dt>Hora</dt>
                <dd>{hora}</dd>
                <dt>Huella</dt>
                <dd>
                  <code className="huella" title={`SHA-256: ${f.huella_sha256}`}>
                    {huellaAbreviada(f.huella_sha256)}
                  </code>
                </dd>
              </dl>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

type CuerpoDespacho = { items: { item_id: string; cantidad: number }[] };
type CuerpoActa = { items: { item_id: string; cantidad_recibida: number; observacion?: string }[] };

export function DetalleSolicitud() {
  const { id } = useParams<{ id: string }>();
  // Mensaje que deja otra pantalla al llegar aquí (por ejemplo, "Solicitud enviada", T103).
  const exitoInicial = (useLocation().state as { exito?: string } | null)?.exito ?? null;
  const [req, setReq] = useState<Requerimiento | null>(null);
  const [firmas, setFirmas] = useState<Firma[]>([]);
  const [verificacion, setVerificacion] = useState<Verificacion | null>(null);
  const [historial, setHistorial] = useState<EntradaHistorial[] | null>(null);
  const [documento, setDocumento] = useState<Documento | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(exitoInicial);
  const [enviando, setEnviando] = useState(false);
  const [rechazando, setRechazando] = useState(false);
  const [anulando, setAnulando] = useState(false);
  const [confirmandoFirma, setConfirmandoFirma] = useState(false);
  const [stock, setStock] = useState<Record<string, number> | null>(null);

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

  // El almacenero ve el stock disponible de cada ítem antes de despachar (T105).
  const puedeDespachar = puede(req, 'DESPACHAR');
  useEffect(() => {
    if (!puedeDespachar) return;
    let vigente = true;
    stockPorItem()
      .then((disponible) => {
        if (vigente) setStock(disponible);
      })
      .catch(() => {
        if (vigente) setStock({});
      });
    return () => {
      vigente = false;
    };
  }, [puedeDespachar]);

  /** Ejecuta una acción, muestra el resultado y recarga el detalle. */
  async function ejecutar<T>(accion: () => Promise<T>, mensaje: (r: T) => string) {
    setEnviando(true);
    setErrorAccion(null);
    setExito(null);
    setVerificacion(null);
    setHistorial(null);
    setDocumento(null);
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
      setConfirmandoFirma(false);
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

  async function verDocumento() {
    if (documento) {
      setDocumento(null);
      return;
    }
    setErrorAccion(null);
    try {
      setDocumento(await obtenerDocumento(id ?? ''));
    } catch (e: unknown) {
      setErrorAccion(textoError(e));
    }
  }

  return (
    <main className="contenedor">
      <Link className="volver" to="/bandeja">
        <ArrowLeft size={16} />
        Volver a la bandeja
      </Link>
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      {!req && !error ? <Cargando /> : null}
      {req ? (
        <article>
          <header className="panel ficha">
            <p className="antetitulo">
              Requerimiento · {req.categoria === 'INTENDENCIA' ? 'Intendencia' : 'Material de guerra'}
            </p>
            <h2 className="ficha__titulo">
              {req.codigo} <EstadoEtiqueta estado={req.estado} />
            </h2>
            <ul className="ficha__datos">
              <li>
                <Building2 size={16} />
                Unidad: {req.unidad.nombre} ({req.unidad.codigo})
              </li>
              {req.almacen ? (
                <li>
                  <Warehouse size={16} />
                  Almacén: {req.almacen.nombre}
                </li>
              ) : null}
              {req.monto_total ? (
                <li>
                  <Coins size={16} />
                  Monto: {formatoSoles(req.monto_total)}
                </li>
              ) : null}
            </ul>
          </header>

          <section className="seccion" aria-labelledby="titulo-items">
            <h3 id="titulo-items">
              <Package />
              Ítems ({req.items.length})
            </h3>
            <ul className="lista">
              {req.items.map((i) => (
                <li key={i.item.id} className="lista__fila">
                  <span className="item__nombre">
                    <Package size={16} />
                    {i.item.codigo} — {i.item.nombre}
                  </span>
                  <strong>{cantidadConUnidad(i.cantidad_solicitada, i.item.unidad_medida)}</strong>
                  {i.cantidad_despachada != null || i.cantidad_recibida != null || i.observacion ? (
                    <span className="item__detalle">
                      {i.cantidad_despachada != null ? (
                        <span>
                          Despachado: {cantidadConUnidad(i.cantidad_despachada, i.item.unidad_medida)}
                        </span>
                      ) : null}
                      {i.cantidad_recibida != null ? (
                        <span>
                          Recibido: {cantidadConUnidad(i.cantidad_recibida, i.item.unidad_medida)}
                        </span>
                      ) : null}
                      {i.observacion ? <span>Observación: {i.observacion}</span> : null}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>

          {exito ? <Mensaje tipo="exito">{exito}</Mensaje> : null}
          {errorAccion ? <Mensaje tipo="error">{errorAccion}</Mensaje> : null}
          {enviando ? <Cargando /> : null}

          <div className="formulario__acciones acciones">
            {puede(req, 'FIRMAR') ? (
              <button
                type="button"
                className="boton"
                disabled={enviando}
                onClick={() => setConfirmandoFirma(true)}
              >
                <Feather size={18} />
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
                <CircleX size={18} />
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
                <Ban size={18} />
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
                <ShieldCheck size={18} />
                Verificar
              </button>
            ) : null}
          </div>
          {confirmandoFirma ? (
            <DialogoConfirmacion
              titulo="¿Firmar la solicitud?"
              advertencia={ADVERTENCIA_FIRMA}
              confirmar="Sí, firmar"
              enviando={enviando}
              onConfirmar={firmar}
              onCancelar={() => setConfirmandoFirma(false)}
            >
              <p>
                Va a aprobar con su firma digital la solicitud {req.codigo}, que está en "
                {etiquetaEstado(req.estado)}".
              </p>
            </DialogoConfirmacion>
          ) : null}
          {rechazando ? (
            <DialogoMotivo
              titulo="Rechazar la solicitud"
              advertencia={ADVERTENCIA_RECHAZO}
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
            <FormularioDespacho
              items={req.items}
              stock={stock}
              enviando={enviando}
              onDespachar={despachar}
            />
          ) : null}
          {puede(req, 'FIRMAR_ACTA') ? (
            <FormularioActa items={req.items} enviando={enviando} onFirmar={firmarActa} />
          ) : null}

          {verificacion ? <ResultadoVerificacion verificacion={verificacion} /> : null}
          <ListaFirmas firmas={firmas} />

          <section className="seccion" aria-labelledby="titulo-documento">
            <p className="antetitulo">Documento oficial</p>
            <h3 id="titulo-documento">
              <FileText />
              Documento
            </h3>
            <div className="acciones">
              <button
                type="button"
                className="boton--secundario"
                aria-expanded={documento !== null}
                onClick={() => void verDocumento()}
              >
                <FileText size={18} />
                {documento ? 'Ocultar documento' : 'Ver documento'}
              </button>
            </div>
            {documento ? <DocumentoOficial documento={documento} /> : null}
          </section>

          <section className="seccion" aria-labelledby="titulo-historial">
            <p className="antetitulo">Conducto regular</p>
            <h3 id="titulo-historial">
              <Clock />
              Línea de tiempo
            </h3>
            <button
              type="button"
              className="boton--secundario"
              aria-expanded={historial !== null}
              onClick={() => void verHistorial()}
            >
              <Clock size={18} />
              {historial ? 'Ocultar línea de tiempo' : 'Ver línea de tiempo'}
            </button>
            {historial ? <LineaTiempo entradas={historial} /> : null}
          </section>
        </article>
      ) : null}
    </main>
  );
}
