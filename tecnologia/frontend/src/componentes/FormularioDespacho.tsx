import { useState } from 'react';
import type { ItemRequerimiento } from '../api/tipos';
import { cantidadesIniciales, cuerpoDespacho, validarDespacho } from '../logica/despacho';
import { Campo } from './Formulario';
import { Mensaje } from './Mensaje';

interface Props {
  items: ItemRequerimiento[];
  enviando?: boolean;
  onDespachar: (cuerpo: ReturnType<typeof cuerpoDespacho>) => void;
}

/**
 * Despacho (T071): una cantidad por ítem, con lo solicitado como valor inicial y como máximo.
 * No deja enviar cantidades fuera de rango; el stock lo valida la API.
 */
export function FormularioDespacho({ items, enviando = false, onDespachar }: Props) {
  const [cantidades, setCantidades] = useState(() => cantidadesIniciales(items));
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | undefined>();

  function despachar() {
    const resultado = validarDespacho(items, cantidades);
    setErrores(resultado.errores);
    setGeneral(resultado.general);
    if (resultado.valido) onDespachar(cuerpoDespacho(items, cantidades));
  }

  return (
    <section className="dialogo" aria-labelledby="titulo-despacho">
      <h3 id="titulo-despacho">Despachar</h3>
      {general ? <Mensaje tipo="aviso">{general}</Mensaje> : null}
      <fieldset className="formulario__campos" disabled={enviando}>
        {items.map((i) => {
          const id = `despacho-${i.item.id}`;
          return (
            <Campo
              key={i.item.id}
              id={id}
              etiqueta={`${i.item.codigo} — ${i.item.nombre} (solicitado: ${i.cantidad_solicitada})`}
              error={errores[i.item.id]}
            >
              <input
                id={id}
                type="number"
                inputMode="numeric"
                min={0}
                max={i.cantidad_solicitada}
                step={1}
                value={cantidades[i.item.id] ?? ''}
                aria-invalid={errores[i.item.id] ? true : undefined}
                aria-describedby={errores[i.item.id] ? `${id}-error` : undefined}
                onChange={(e) => setCantidades({ ...cantidades, [i.item.id]: e.target.value })}
              />
            </Campo>
          );
        })}
        <div className="formulario__acciones">
          <button type="button" className="boton" onClick={despachar}>
            {enviando ? 'Despachando…' : 'Confirmar despacho'}
          </button>
        </div>
      </fieldset>
    </section>
  );
}
