import { useEffect, useRef, useState } from 'react';
import type { ItemRequerimiento } from '../api/tipos';
import { ADVERTENCIA_DESPACHO } from '../logica/acciones';
import { cantidadesIniciales, cuerpoDespacho, validarDespacho } from '../logica/despacho';
import { cantidadConUnidad } from '../logica/formato';
import { DialogoConfirmacion } from './DialogoConfirmacion';
import { Campo } from './Formulario';
import { Mensaje } from './Mensaje';

interface Props {
  items: ItemRequerimiento[];
  /** Stock disponible por item_id en el almacén; null mientras carga o si no se pudo leer. */
  stock?: Record<string, number> | null;
  enviando?: boolean;
  onDespachar: (cuerpo: ReturnType<typeof cuerpoDespacho>) => void;
}

/**
 * Despacho (T071, T100, T105): una cantidad por ítem, con lo solicitado como valor inicial y como
 * máximo, y el stock disponible de cada ítem a la vista. Antes de enviar pide una confirmación,
 * porque el despacho descuenta el stock y no se puede deshacer. El stock lo vuelve a validar la API.
 */
export function FormularioDespacho({ items, stock = null, enviando = false, onDespachar }: Props) {
  const [cantidades, setCantidades] = useState(() => cantidadesIniciales(items));
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | undefined>();
  const [confirmando, setConfirmando] = useState(false);

  // Al terminar un envío (con o sin error) se cierra la confirmación; si hubo error, el usuario
  // ve el mensaje y puede corregir y volver a intentar.
  const estabaEnviando = useRef(enviando);
  useEffect(() => {
    if (estabaEnviando.current && !enviando) setConfirmando(false);
    estabaEnviando.current = enviando;
  }, [enviando]);

  function revisar() {
    const resultado = validarDespacho(items, cantidades);
    setErrores(resultado.errores);
    setGeneral(resultado.general);
    if (resultado.valido) setConfirmando(true);
  }

  const superaStock = (itemId: string) =>
    stock !== null && itemId in stock && Number(cantidades[itemId]) > stock[itemId];

  return (
    <section className="dialogo" aria-labelledby="titulo-despacho">
      <h3 id="titulo-despacho">Despachar</h3>
      {general ? <Mensaje tipo="aviso">{general}</Mensaje> : null}
      <fieldset className="formulario__campos" disabled={enviando || confirmando}>
        {items.map((i) => {
          const id = `despacho-${i.item.id}`;
          const disponible = stock?.[i.item.id];
          return (
            <div key={i.item.id} className="despacho__linea">
              <Campo
                id={id}
                etiqueta={`${i.item.codigo} — ${i.item.nombre} (solicitado: ${cantidadConUnidad(
                  i.cantidad_solicitada,
                  i.item.unidad_medida,
                )})`}
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
                  aria-describedby={`${id}-stock${errores[i.item.id] ? ` ${id}-error` : ''}`}
                  onChange={(e) => setCantidades({ ...cantidades, [i.item.id]: e.target.value })}
                />
              </Campo>
              <p id={`${id}-stock`} className="despacho__stock">
                {stock === null
                  ? 'Stock disponible: consultando…'
                  : disponible === undefined
                    ? 'Stock disponible: sin registro en el almacén'
                    : `Stock disponible: ${cantidadConUnidad(disponible, i.item.unidad_medida)}`}
              </p>
              {superaStock(i.item.id) ? (
                <p className="despacho__aviso">
                  La cantidad supera el stock disponible: el despacho será rechazado.
                </p>
              ) : null}
            </div>
          );
        })}
        <div className="formulario__acciones">
          <button type="button" className="boton" onClick={revisar}>
            Confirmar despacho
          </button>
        </div>
      </fieldset>
      {confirmando ? (
        <DialogoConfirmacion
          titulo="¿Despachar estas cantidades?"
          advertencia={ADVERTENCIA_DESPACHO}
          confirmar="Sí, despachar"
          enviando={enviando}
          onConfirmar={() => onDespachar(cuerpoDespacho(items, cantidades))}
          onCancelar={() => setConfirmando(false)}
        >
          <ul>
            {items.map((i) => (
              <li key={i.item.id}>
                {i.item.codigo} — {i.item.nombre}:{' '}
                {cantidadConUnidad(Number(cantidades[i.item.id]), i.item.unidad_medida)}
              </li>
            ))}
          </ul>
        </DialogoConfirmacion>
      ) : null}
    </section>
  );
}
