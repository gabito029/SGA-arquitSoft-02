interface Props {
  texto?: string;
}

/** Indicador de carga, anunciado a los lectores de pantalla. */
export function Cargando({ texto = 'Cargando…' }: Props) {
  return (
    <p className="cargando" role="status" aria-live="polite">
      <span className="cargando__indicador" aria-hidden="true" />
      {texto}
    </p>
  );
}
