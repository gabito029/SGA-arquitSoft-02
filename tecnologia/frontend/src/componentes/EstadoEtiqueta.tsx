import type { EstadoRequerimiento } from '../api/tipos';
import { etiquetaEstado, tonoEstado } from '../logica/estados';

interface Props {
  estado: EstadoRequerimiento;
}

/** Etiqueta del estado con el nombre que usa la interfaz (spec.md, tabla de estados). */
export function EstadoEtiqueta({ estado }: Props) {
  return (
    <span className={`estado estado--${tonoEstado(estado)}`} data-estado={estado}>
      {etiquetaEstado(estado)}
    </span>
  );
}
