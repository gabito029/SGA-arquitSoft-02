import { useEffect, useRef, useState } from 'react';
import type { ItemRequerimiento } from '../api/tipos';
import {
  cuerpoActa,
  hayDiferencia,
  OBSERVACION_MAXIMA,
  recepcionInicial,
  validarActa,
} from '../logica/acta';
import { ADVERTENCIA_ACTA } from '../logica/acciones';
import { cantidadConUnidad } from '../logica/formato';
import { DialogoConfirmacion } from './DialogoConfirmacion';
import { Campo } from './Formulario';

interface Props {
  items: ItemRequerimiento[];
  enviando?: boolean;
  onFirmar: (cuerpo: ReturnType<typeof cuerpoActa>) => void;
}

/**
 * Firmar el acta (T079, T100): cantidad recibida y observación por ítem. Las líneas con diferencias
 * respecto de lo despachado se resaltan, y antes de firmar se pide una confirmación, porque la
 * firma no se puede deshacer.
 */
export function FormularioActa({ items, enviando = false, onFirmar }: Props) {
  const [recepcion, setRecepcion] = useState(() => recepcionInicial(items));
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [confirmando, setConfirmando] = useState(false);

  // Al terminar un envío (con o sin error) se cierra la confirmación; si hubo error, el usuario
  // ve el mensaje y puede corregir y volver a intentar.
  const estabaEnviando = useRef(enviando);
  useEffect(() => {
    if (estabaEnviando.current && !enviando) setConfirmando(false);
    estabaEnviando.current = enviando;
  }, [enviando]);

  function cambiar(itemId: string, campo: 'cantidad' | 'observacion', valor: string) {
    setRecepcion({ ...recepcion, [itemId]: { ...recepcion[itemId], [campo]: valor } });
  }

  function firmar() {
    const encontrados = validarActa(items, recepcion);
    setErrores(encontrados);
    if (Object.keys(encontrados).length === 0) setConfirmando(true);
  }

  const conDiferencias = items.filter((i) => hayDiferencia(i, recepcion[i.item.id])).length;

  return (
    <section className="dialogo" aria-labelledby="titulo-acta">
      <h3 id="titulo-acta">Firmar acta de recepción</h3>
      <fieldset className="formulario__campos" disabled={enviando || confirmando}>
        {items.map((i) => {
          const id = `recibido-${i.item.id}`;
          const diferencia = hayDiferencia(i, recepcion[i.item.id]);
          return (
            <div
              key={i.item.id}
              className={diferencia ? 'acta__linea acta__linea--diferencia' : 'acta__linea'}
              data-testid={`linea-${i.item.codigo}`}
            >
              <Campo
                id={id}
                etiqueta={`${i.item.codigo} — recibido (despachado: ${cantidadConUnidad(
                  i.cantidad_despachada ?? 0,
                  i.item.unidad_medida,
                )})`}
                error={errores[i.item.id]}
              >
                <input
                  id={id}
                  type="number"
                  inputMode="numeric"
                  min={0}
                  step={1}
                  value={recepcion[i.item.id]?.cantidad ?? ''}
                  aria-invalid={errores[i.item.id] ? true : undefined}
                  aria-describedby={errores[i.item.id] ? `${id}-error` : undefined}
                  onChange={(e) => cambiar(i.item.id, 'cantidad', e.target.value)}
                />
              </Campo>
              {diferencia ? <p className="acta__aviso">Diferencia con lo despachado</p> : null}
              <Campo id={`observacion-${i.item.id}`} etiqueta={`${i.item.codigo} — observación`}>
                <input
                  id={`observacion-${i.item.id}`}
                  type="text"
                  maxLength={OBSERVACION_MAXIMA}
                  value={recepcion[i.item.id]?.observacion ?? ''}
                  onChange={(e) => cambiar(i.item.id, 'observacion', e.target.value)}
                />
              </Campo>
            </div>
          );
        })}
        <p>
          {conDiferencias === 0
            ? 'Lo recibido coincide con lo despachado.'
            : `${conDiferencias} ítem(s) con diferencias.`}
        </p>
        <div className="formulario__acciones">
          <button type="button" className="boton" onClick={firmar}>
            {enviando ? 'Firmando…' : 'Firmar acta'}
          </button>
        </div>
      </fieldset>
      {confirmando ? (
        <DialogoConfirmacion
          titulo="¿Firmar el acta de recepción?"
          advertencia={ADVERTENCIA_ACTA}
          confirmar="Sí, firmar el acta"
          enviando={enviando}
          onConfirmar={() => onFirmar(cuerpoActa(items, recepcion))}
          onCancelar={() => setConfirmando(false)}
        >
          <p>
            {conDiferencias === 0
              ? 'Lo recibido coincide con lo despachado.'
              : `Se registrarán diferencias en ${conDiferencias} ítem(s).`}
          </p>
        </DialogoConfirmacion>
      ) : null}
    </section>
  );
}
