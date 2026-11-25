import { TriangleExclamationPoint } from 'lucide-react';
import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';

interface Props {
  titulo: string;
  /** Lo que se va a hacer, con el detalle necesario para decidir. */
  children: ReactNode;
  /** Por qué conviene revisar antes (por ejemplo, que la firma no se puede deshacer). */
  advertencia: string;
  confirmar: string;
  enviando?: boolean;
  /** Mientras es verdadero, el botón de confirmar queda desactivado (p. ej., falta la revisión). */
  bloqueado?: boolean;
  onConfirmar: () => void;
  onCancelar: () => void;
}

/**
 * Paso de confirmación dentro de la página (T100). Nunca se usa `window.confirm` ni `alert`: el
 * diálogo es accesible (role="alertdialog", foco en el diálogo al abrir, Escape cancela) y explica
 * que la acción no se puede deshacer.
 */
export function DialogoConfirmacion({
  titulo,
  children,
  advertencia,
  confirmar,
  enviando = false,
  bloqueado = false,
  onConfirmar,
  onCancelar,
}: Props) {
  const dialogo = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dialogo.current?.focus();
  }, []);

  return (
    <div
      ref={dialogo}
      className="dialogo dialogo--confirmacion"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirmacion-titulo"
      aria-describedby="confirmacion-advertencia"
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === 'Escape' && !enviando) onCancelar();
      }}
    >
      <h3 id="confirmacion-titulo">
        <TriangleExclamationPoint />
        {titulo}
      </h3>
      <div>{children}</div>
      <p id="confirmacion-advertencia" className="dialogo__advertencia">
        {advertencia}
      </p>
      <div className="formulario__acciones">
        <button
          type="button"
          className="boton"
          disabled={enviando || bloqueado}
          onClick={onConfirmar}
        >
          {enviando ? 'Procesando…' : confirmar}
        </button>
        <button
          type="button"
          className="boton--secundario"
          disabled={enviando}
          onClick={onCancelar}
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}

