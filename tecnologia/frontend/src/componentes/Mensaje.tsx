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

/** Mensaje accesible: los errores se anuncian de inmediato (role="alert"). */
export function Mensaje({ tipo, children }: Props) {
  return (
    <div className={`mensaje mensaje--${tipo}`} role={tipo === 'error' ? 'alert' : 'status'}>
      <strong className="mensaje__titulo">{TITULOS[tipo]}:</strong> {children}
    </div>
  );
}
