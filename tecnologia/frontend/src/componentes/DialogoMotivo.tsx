import { FileText } from 'lucide-react';
import { useState } from 'react';
import type { ReactNode } from 'react';
import { MOTIVO_MAXIMO, validarMotivo } from '../logica/acciones';
import { Campo } from './Formulario';

interface Props {
  titulo: string;
  confirmar: string;
  /** Explica las consecuencias, por ejemplo que el rechazo no se puede deshacer (T100). */
  advertencia?: string;
  /** Mientras es verdadero, el diálogo queda desactivado. */
  enviando?: boolean;
  /** Contenido previo al motivo, por ejemplo el documento a revisar (002, US2). */
  children?: ReactNode;
  /** Mientras es verdadero, el botón de confirmar queda desactivado (p. ej., falta la revisión). */
  bloqueado?: boolean;
  onConfirmar: (motivo: string) => void;
  onCancelar: () => void;
}

/** Diálogo que pide un motivo obligatorio antes de rechazar o anular (FR-015, FR-022). */
export function DialogoMotivo({
  titulo,
  confirmar,
  advertencia,
  enviando = false,
  children,
  bloqueado = false,
  onConfirmar,
  onCancelar,
}: Props) {
  const [motivo, setMotivo] = useState('');
  const [error, setError] = useState<string | undefined>();

  function aceptar() {
    const problema = validarMotivo(motivo);
    if (problema) {
      setError(problema);
      return;
    }
    onConfirmar(motivo.trim());
  }

  return (
    <div className="dialogo" role="dialog" aria-modal="true" aria-labelledby="dialogo-titulo">
      <h3 id="dialogo-titulo">
        <FileText />
        {titulo}
      </h3>
      {advertencia ? <p className="dialogo__advertencia">{advertencia}</p> : null}
      {children}
      <fieldset className="formulario__campos" disabled={enviando}>
        <Campo id="motivo" etiqueta="Motivo" error={error}>
          <textarea
            id="motivo"
            value={motivo}
            maxLength={MOTIVO_MAXIMO}
            rows={3}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? 'motivo-error' : undefined}
            onChange={(e) => {
              setMotivo(e.target.value);
              setError(undefined);
            }}
          />
        </Campo>
        <div className="formulario__acciones">
          <button type="button" className="boton" disabled={bloqueado} onClick={aceptar}>
            {enviando ? 'Enviando…' : confirmar}
          </button>
          <button type="button" className="boton--secundario" onClick={onCancelar}>
            Cancelar
          </button>
        </div>
      </fieldset>
    </div>
  );
}
