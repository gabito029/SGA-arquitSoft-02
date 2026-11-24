import {
  Ban,
  CircleCheck,
  CircleDot,
  CircleX,
  FilePen,
  Hourglass,
  PackageCheck,
  Truck,
  type LucideIcon,
} from 'lucide-react';
import type { EstadoRequerimiento } from '../api/tipos';
import { etiquetaEstado, tonoEstado } from '../logica/estados';

const ICONOS: Record<EstadoRequerimiento, LucideIcon> = {
  BORRADOR: FilePen,
  PENDIENTE_VB_UNIDAD: Hourglass,
  PENDIENTE_CONFORMIDAD: Hourglass,
  PENDIENTE_AUTORIZACION_COLOGE: Hourglass,
  PENDIENTE_APROBACION: Hourglass,
  APROBADA: CircleCheck,
  EN_TRANSITO: Truck,
  CONFIRMADA: PackageCheck,
  RECHAZADA: CircleX,
  ANULADA: Ban,
};

interface Props {
  estado: EstadoRequerimiento;
}

/** Insignia del estado con su ícono (T108) y el nombre que usa la interfaz (spec.md). */
export function EstadoEtiqueta({ estado }: Props) {
  const Icono = ICONOS[estado] ?? CircleDot;
  return (
    <span className={`estado estado--${tonoEstado(estado)}`} data-estado={estado}>
      <Icono size={14} strokeWidth={2.25} />
      {etiquetaEstado(estado)}
    </span>
  );
}
