import type { Verificacion } from '../api/tipos';
import { ETIQUETAS_VERIFICACION } from '../logica/acta';
import { ETIQUETAS_NIVEL } from '../logica/estados';
import { Mensaje } from './Mensaje';

function fecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' });
}

/**
 * Resultado de la verificación (FR-024, FR-025): ALTERADA se muestra como alerta e INTEGRA como
 * éxito, con el resultado de cada firma, su firmante y su fecha.
 */
export function ResultadoVerificacion({ verificacion }: { verificacion: Verificacion }) {
  const integra = verificacion.resultado === 'INTEGRA';
  return (
    <section aria-labelledby="titulo-verificacion">
      <h3 id="titulo-verificacion">Verificación de integridad</h3>
      {integra ? (
        <Mensaje tipo="exito">Todas las firmas están íntegras.</Mensaje>
      ) : (
        <Mensaje tipo="error">
          Se detectó una alteración: los datos firmados no coinciden con los registrados.
        </Mensaje>
      )}
      <ul className="lista">
        {verificacion.firmas.map((f) => (
          <li key={f.firma_id} className="lista__fila">
            <span>{ETIQUETAS_NIVEL[f.nivel]}</span>
            <span
              className={`estado estado--${f.resultado === 'INTEGRA' ? 'exito' : 'alerta'}`}
            >
              {ETIQUETAS_VERIFICACION[f.resultado]}
            </span>
            <span>{f.firmante}</span>
            <time dateTime={f.firmado_en}>{fecha(f.firmado_en)}</time>
          </li>
        ))}
      </ul>
    </section>
  );
}
