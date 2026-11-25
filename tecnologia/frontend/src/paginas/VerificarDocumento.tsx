// Verificar un PDF (incremento 002, US5: FR-016 a FR-019; EQ-02). El usuario elige el PDF que
// recibió y el sistema responde si es Auténtico o Alterado, con el motivo, el código, el
// requerimiento y los sellos que contiene.
import { ArrowLeft, ShieldCheck, ShieldExclamationPoint, Upload } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ErrorApi } from '../api/cliente';
import { validarArchivoPdf, verificarPdf } from '../api/pdf';
import type { VerificacionPdf } from '../api/tipos';
import { Cargando } from '../componentes/Cargando';
import { Mensaje } from '../componentes/Mensaje';
import { ETIQUETAS_NIVEL } from '../logica/estados';
import { fechaHora } from '../logica/formato';
import { MENSAJE_GENERICO } from '../logica/mensajes';

function Resultado({ verificacion }: { verificacion: VerificacionPdf }) {
  const autentico = verificacion.resultado === 'AUTENTICO';
  const doc = verificacion.documento;
  const emision = doc ? fechaHora(doc.emitido_en) : null;
  return (
    <section
      className={`panel resultado-pdf resultado-pdf--${autentico ? 'autentico' : 'alterado'}`}
      aria-live="polite"
      aria-labelledby="titulo-resultado"
    >
      <h3 id="titulo-resultado">
        {autentico ? <ShieldCheck /> : <ShieldExclamationPoint />}
        <span className={`estado estado--${autentico ? 'aprobada' : 'rechazada'}`}>
          {autentico ? 'Auténtico' : 'Alterado'}
        </span>
      </h3>
      <p>{verificacion.motivo}</p>
      {doc ? (
        <dl className="documento__datos">
          <dt>Código de verificación</dt>
          <dd>
            <code>{doc.codigo_verificacion}</code>
          </dd>
          <dt>Documento</dt>
          <dd>{doc.tipo === 'ACTA' ? 'Acta de recepción' : 'Requerimiento'}</dd>
          <dt>Requerimiento</dt>
          <dd>
            <Link to={`/solicitudes/${doc.requerimiento_id}`}>{doc.requerimiento_codigo}</Link>
          </dd>
          <dt>Emitido</dt>
          <dd>
            {emision?.fecha} · {emision?.hora}
          </dd>
          <dt>Sellos</dt>
          <dd>
            <ul className="lista-simple">
              {doc.sellos.map((s) => (
                <li key={s.firma_id}>
                  {ETIQUETAS_NIVEL[s.nivel]}: {s.decision === 'APROBAR' ? 'aprobó' : 'rechazó'}{' '}
                  {s.firmante}
                </li>
              ))}
            </ul>
          </dd>
        </dl>
      ) : null}
    </section>
  );
}

export function VerificarDocumento() {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [verificacion, setVerificacion] = useState<VerificacionPdf | null>(null);

  async function verificar(e: React.FormEvent) {
    e.preventDefault();
    setVerificacion(null);
    const problema = validarArchivoPdf(archivo);
    if (problema || !archivo) {
      setError(problema);
      return;
    }
    setError(null);
    setEnviando(true);
    try {
      setVerificacion(await verificarPdf(archivo));
    } catch (e: unknown) {
      setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="contenedor">
      <Link className="volver" to="/bandeja">
        <ArrowLeft size={16} />
        Volver a la bandeja
      </Link>
      <p className="antetitulo">Integridad documental</p>
      <h2 className="barra__titulo">
        <ShieldCheck />
        Verificar PDF
      </h2>
      <p>
        Suba un PDF emitido por el SGA para comprobar que es auténtico: que no cambió ni un byte
        desde su emisión y que las firmas que contiene siguen íntegras.
      </p>
      <form className="panel formulario" onSubmit={(e) => void verificar(e)} noValidate>
        <label htmlFor="archivo-pdf" className="campo__etiqueta">
          Archivo PDF (máximo 5 MB)
        </label>
        <input
          id="archivo-pdf"
          type="file"
          accept="application/pdf,.pdf"
          aria-invalid={error ? true : undefined}
          onChange={(e) => {
            setArchivo(e.target.files?.[0] ?? null);
            setError(null);
            setVerificacion(null);
          }}
        />
        <div className="formulario__acciones">
          <button type="submit" className="boton" disabled={enviando}>
            <Upload size={18} />
            {enviando ? 'Verificando…' : 'Verificar'}
          </button>
        </div>
      </form>
      {enviando ? <Cargando /> : null}
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      {verificacion ? <Resultado verificacion={verificacion} /> : null}
    </main>
  );
}
