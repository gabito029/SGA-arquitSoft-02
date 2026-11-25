// Documento oficial del requerimiento o del acta (incremento 002, FR-001 a FR-003 y FR-014): el
// mismo contenido que imprime el PDF. Encabezado, tabla de ítems y bloque de firmas con un sello
// digital por firma (nivel, decisión, cargo, órgano, fecha, hora, método y huella abreviada).
import { FileText, Stamp } from 'lucide-react';
import type { Documento, Referencia, Sello } from '../api/tipos';
import { ETIQUETAS_NIVEL } from '../logica/estados';
import { fechaHora, huellaAbreviada } from '../logica/formato';
import { ETIQUETAS_ROL } from '../logica/historial';

function referencia(r?: Referencia | null): string {
  return r ? `${r.codigo} · ${r.nombre}` : '—';
}

function SelloDigital({ sello }: { sello: Sello }) {
  const aprobo = sello.decision === 'APROBAR';
  const { fecha, hora } = fechaHora(sello.firmado_en);
  return (
    <li className={`sello sello--${aprobo ? 'aprobado' : 'rechazado'}`}>
      <p className="sello__cabecera">
        <Stamp size={16} />
        <span>{ETIQUETAS_NIVEL[sello.nivel]}</span>
      </p>
      <p className="sello__firmante">
        {aprobo ? 'Aprobó' : 'Rechazó'}: {sello.firmante}
      </p>
      <p className="sello__cargo">
        {ETIQUETAS_ROL[sello.rol]} · {referencia(sello.organo)}
      </p>
      <dl className="sello__datos">
        <dt>Fecha</dt>
        <dd>
          <time dateTime={sello.firmado_en}>{fecha}</time>
        </dd>
        <dt>Hora</dt>
        <dd>{hora}</dd>
        <dt>Método</dt>
        <dd>{sello.metodo}</dd>
        <dt>Huella</dt>
        <dd>
          <code className="huella" title={`SHA-256: ${sello.huella_sha256}`}>
            {huellaAbreviada(sello.huella_sha256)}
          </code>
        </dd>
      </dl>
      {sello.motivo ? <p className="sello__motivo">Motivo: {sello.motivo}</p> : null}
    </li>
  );
}

export function DocumentoOficial({ documento }: { documento: Documento }) {
  const esActa = documento.tipo === 'ACTA';
  const titulo = esActa ? 'Acta de recepción' : 'Requerimiento';
  const fecha = documento.fecha ? fechaHora(documento.fecha).fecha : '—';
  return (
    <article className="documento" aria-label={`Documento oficial: ${titulo} ${documento.codigo}`}>
      <header className="documento__encabezado">
        <p className="documento__sistema">SGA · Sistema de Gestión de Almacén con Firma Digital</p>
        <h4 className="documento__titulo">
          <FileText size={18} />
          {titulo}
        </h4>
        <dl className="documento__datos">
          <dt>Número</dt>
          <dd>{documento.codigo}</dd>
          <dt>Fecha</dt>
          <dd>{fecha}</dd>
          <dt>Unidad solicitante</dt>
          <dd>{referencia(documento.unidad)}</dd>
          <dt>Gran Unidad</dt>
          <dd>{referencia(documento.gran_unidad)}</dd>
          <dt>Almacén</dt>
          <dd>{referencia(documento.almacen)}</dd>
        </dl>
      </header>

      <div className="documento__tabla">
        <table className="tabla">
          <caption>Ítems</caption>
          <thead>
            <tr>
              <th scope="col">Código</th>
              <th scope="col">Descripción</th>
              <th scope="col">U. M.</th>
              <th scope="col">Solicitado</th>
              {esActa ? (
                <>
                  <th scope="col">Despachado</th>
                  <th scope="col">Recibido</th>
                  <th scope="col">Observación</th>
                </>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {documento.items.map((i) => (
              <tr key={i.codigo}>
                <td>{i.codigo}</td>
                <td>{i.descripcion}</td>
                <td>{i.unidad_medida}</td>
                <td>{i.cantidad_solicitada}</td>
                {esActa ? (
                  <>
                    <td>{i.cantidad_despachada ?? '—'}</td>
                    <td>{i.cantidad_recibida ?? '—'}</td>
                    <td>{i.observacion || '—'}</td>
                  </>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {esActa ? (
        <p className="documento__nota">
          {documento.tiene_diferencias
            ? 'Se registraron diferencias entre lo despachado y lo recibido.'
            : 'Lo recibido coincide con lo despachado.'}
        </p>
      ) : null}

      <section aria-label="Firmas del documento">
        <p className="antetitulo">Firmas (sellos digitales)</p>
        {documento.sellos.length === 0 ? (
          <p>Todavía no hay firmas.</p>
        ) : (
          <ul className="sellos">
            {documento.sellos.map((s) => (
              <SelloDigital key={s.firma_id} sello={s} />
            ))}
          </ul>
        )}
      </section>
      <p className="documento__huella">
        Huella SHA-256 del documento:{' '}
        <code className="huella" title={documento.huella_contenido}>
          {huellaAbreviada(documento.huella_contenido)}
        </code>
      </p>
    </article>
  );
}
