import { ShieldCheck, ShieldExclamationPoint } from 'lucide-react';
import type { Verificacion } from '../api/tipos';
import { ETIQUETAS_VERIFICACION } from '../logica/acta';
import { ETIQUETAS_NIVEL } from '../logica/estados';
import { fechaHora } from '../logica/formato';
import { Mensaje } from './Mensaje';

/**
 * Resultado de la verificación (FR-024, FR-025): ALTERADA se muestra como alerta e INTEGRA como
 * éxito, con el resultado de cada firma, su firmante y su fecha.
 */
export function ResultadoVerificacion({ verificacion }: { verificacion: Verificacion }) {
  const integra = verificacion.resultado === 'INTEGRA';
  return (
    <section className="seccion" aria-labelledby="titulo-verificacion">
      <h3 id="titulo-verificacion">
        {integra ? <ShieldCheck /> : <ShieldExclamationPoint />}
        Verificación de integridad
      </h3>
      {integra ? (
        <Mensaje tipo="exito">Todas las firmas están íntegras.</Mensaje>
      ) : (
        <Mensaje tipo="error">
          Se detectó una alteración: los datos firmados no coinciden con los registrados.
        </Mensaje>
      )}
      <ul className="lista">
        {verificacion.firmas.map((f) => {
          const integraFirma = f.resultado === 'INTEGRA';
          const { fecha, hora } = fechaHora(f.firmado_en);
          return (
            <li key={f.firma_id} className="lista__fila">
              <span>{ETIQUETAS_NIVEL[f.nivel]}</span>
              <span className={`estado estado--${integraFirma ? 'aprobada' : 'rechazada'}`}>
                {integraFirma ? <ShieldCheck size={14} /> : <ShieldExclamationPoint size={14} />}
                {ETIQUETAS_VERIFICACION[f.resultado]}
              </span>
              <span>{f.firmante}</span>
              <time dateTime={f.firmado_en}>
                {fecha} · {hora}
              </time>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
