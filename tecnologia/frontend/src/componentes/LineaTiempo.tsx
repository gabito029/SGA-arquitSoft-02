import {
  Ban,
  CircleX,
  ClipboardCheck,
  Feather,
  FilePlus,
  Lock,
  Send,
  Truck,
  type LucideIcon,
} from 'lucide-react';
import type { EntradaHistorial } from '../api/tipos';
import { etiquetaEstado, tonoEstado } from '../logica/estados';
import { fechaHora } from '../logica/formato';
import { ETIQUETAS_ACCION_HISTORIAL, ETIQUETAS_ROL, ordenarHistorial } from '../logica/historial';

const ICONOS: Record<EntradaHistorial['accion'], LucideIcon> = {
  CREAR: FilePlus,
  ENVIAR: Send,
  ENVIO_BLOQUEADO: Lock,
  FIRMAR: Feather,
  RECHAZAR: CircleX,
  ANULAR: Ban,
  DESPACHAR: Truck,
  FIRMAR_ACTA: ClipboardCheck,
};

/**
 * Línea de tiempo (T084, T111; FR-026 a FR-028): secuencia vertical del conducto regular con un
 * ícono por paso, quién actuó, en qué órgano, cuándo, desde qué estado y, si existe, el motivo.
 */
export function LineaTiempo({ entradas }: { entradas: EntradaHistorial[] }) {
  if (entradas.length === 0) return <p>La solicitud todavía no tiene movimientos.</p>;
  return (
    <ol className="linea-tiempo" aria-label="Línea de tiempo">
      {ordenarHistorial(entradas).map((e, indice) => {
        const Icono = ICONOS[e.accion] ?? FilePlus;
        const { fecha, hora } = fechaHora(e.ocurrido_en);
        return (
          <li key={`${e.ocurrido_en}-${indice}`} className="linea-tiempo__paso">
            <span
              className={`linea-tiempo__icono linea-tiempo__icono--${tonoEstado(e.estado_nuevo)}`}
            >
              <Icono size={18} />
            </span>
            <div className="linea-tiempo__cuerpo">
              <strong className="linea-tiempo__accion">
                {ETIQUETAS_ACCION_HISTORIAL[e.accion]}
              </strong>
              <span>
                {e.usuario} · {ETIQUETAS_ROL[e.rol]} · {e.organo.codigo}
              </span>
              <time className="linea-tiempo__meta" dateTime={e.ocurrido_en}>
                {fecha} · {hora}
              </time>
              <span className="linea-tiempo__meta">
                {e.estado_anterior ? `${etiquetaEstado(e.estado_anterior)} → ` : ''}
                {etiquetaEstado(e.estado_nuevo)}
              </span>
              {e.motivo ? <span className="linea-tiempo__motivo">Motivo: {e.motivo}</span> : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
