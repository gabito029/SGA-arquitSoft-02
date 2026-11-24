import type { EntradaHistorial } from '../api/tipos';
import { etiquetaEstado } from '../logica/estados';
import { ETIQUETAS_ACCION_HISTORIAL, ETIQUETAS_ROL, ordenarHistorial } from '../logica/historial';

function fecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' });
}

/**
 * Línea de tiempo (T084; FR-026 a FR-028): cada paso con quién, en qué órgano, cuándo, desde qué
 * estado y, si existe, el motivo.
 */
export function LineaTiempo({ entradas }: { entradas: EntradaHistorial[] }) {
  if (entradas.length === 0) return <p>La solicitud todavía no tiene movimientos.</p>;
  return (
    <ol className="linea-tiempo" aria-label="Línea de tiempo">
      {ordenarHistorial(entradas).map((e, indice) => (
        <li key={`${e.ocurrido_en}-${indice}`} className="linea-tiempo__paso">
          <strong>{ETIQUETAS_ACCION_HISTORIAL[e.accion]}</strong>
          <span>
            {e.usuario} · {ETIQUETAS_ROL[e.rol]} · {e.organo.codigo}
          </span>
          <time dateTime={e.ocurrido_en}>{fecha(e.ocurrido_en)}</time>
          <span>
            {e.estado_anterior ? `${etiquetaEstado(e.estado_anterior)} → ` : ''}
            {etiquetaEstado(e.estado_nuevo)}
          </span>
          {e.motivo ? <span className="linea-tiempo__motivo">Motivo: {e.motivo}</span> : null}
        </li>
      ))}
    </ol>
  );
}
