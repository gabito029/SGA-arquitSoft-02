import { CircleCheck, CircleExclamationPoint, TriangleExclamationPoint } from 'lucide-react';
import type { ReactNode } from 'react';

export type TipoMensaje = 'error' | 'exito' | 'aviso';

interface Props {
  tipo: TipoMensaje;
  children: ReactNode;
}

const TITULOS: Record<TipoMensaje, string> = {
  error: 'Error',
  exito: 'Listo',
  aviso: 'Aviso',
};

const ICONOS = {
  error: CircleExclamationPoint,
  exito: CircleCheck,
  aviso: TriangleExclamationPoint,
} as const;

/** Mensaje accesible: los errores se anuncian de inmediato (role="alert"). */
export function Mensaje({ tipo, children }: Props) {
  const Icono = ICONOS[tipo];
  return (
    <div className={`mensaje mensaje--${tipo}`} role={tipo === 'error' ? 'alert' : 'status'}>
      <Icono />
      <span>
        <strong className="mensaje__titulo">{TITULOS[tipo]}:</strong> {children}
      </span>
    </div>
  );
}
