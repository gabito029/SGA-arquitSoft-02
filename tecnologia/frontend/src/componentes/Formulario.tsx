import type { FormEvent, ReactNode } from 'react';
import { Mensaje } from './Mensaje';

interface Props {
  titulo: string;
  /** Mientras es verdadero, los campos y botones quedan desactivados. */
  enviando?: boolean;
  error?: string | null;
  onEnviar: () => void;
  children: ReactNode;
}

/**
 * Formulario base: evita el envío nativo, desactiva todo mientras espera la respuesta y muestra
 * el error general arriba de los campos.
 */
export function Formulario({ titulo, enviando = false, error, onEnviar, children }: Props) {
  function manejarEnvio(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!enviando) onEnviar();
  }

  return (
    <form className="formulario" onSubmit={manejarEnvio} aria-busy={enviando} noValidate>
      <h2 className="formulario__titulo">{titulo}</h2>
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      <fieldset className="formulario__campos" disabled={enviando}>
        {children}
      </fieldset>
    </form>
  );
}

interface PropsCampo {
  id: string;
  etiqueta: string;
  error?: string;
  children: ReactNode;
}

/** Campo con etiqueta visible y su error asociado (accesibilidad básica, EQ-05). */
export function Campo({ id, etiqueta, error, children }: PropsCampo) {
  return (
    <div className="campo">
      <label className="campo__etiqueta" htmlFor={id}>
        {etiqueta}
      </label>
      {children}
      {error ? (
        <p className="campo__error" id={`${id}-error`} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
