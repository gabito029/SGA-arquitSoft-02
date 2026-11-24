// Nueva solicitud (HU02, RF02; US1). Tres campos por pantalla (categoría, ítem y cantidad; FR-005
// permite 5 como máximo) y la lista de ítems agregados. "Guardar" la deja en Registrada; "Enviar"
// la guarda y la envía por el conducto regular. Si requiere al COLOGE, se muestra el aviso y la
// solicitud queda Registrada (FR-012).
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, ErrorApi } from '../api/cliente';
import type { Categoria, Item, Requerimiento } from '../api/tipos';
import { Cargando } from '../componentes/Cargando';
import { EstadoEtiqueta } from '../componentes/EstadoEtiqueta';
import { Campo, Formulario } from '../componentes/Formulario';
import { Mensaje } from '../componentes/Mensaje';
import { cantidadConUnidad } from '../logica/formato';
import { MENSAJE_GENERICO } from '../logica/mensajes';
import {
  aEntrada,
  esValida,
  leerCantidad,
  validarLinea,
  validarSolicitud,
  type ErroresSolicitud,
  type LineaSolicitud,
} from '../logica/validacionSolicitud';

const CATEGORIAS: { valor: Categoria; etiqueta: string }[] = [
  { valor: 'INTENDENCIA', etiqueta: 'Intendencia' },
  { valor: 'MATERIAL_GUERRA', etiqueta: 'Material de guerra' },
];

type Resultado = { tipo: 'exito' | 'aviso'; texto: string } | null;

export function NuevaSolicitud() {
  const navegar = useNavigate();
  const [categoria, setCategoria] = useState<Categoria>('INTENDENCIA');
  const [catalogo, setCatalogo] = useState<Item[]>([]);
  const [cargandoCatalogo, setCargandoCatalogo] = useState(true);
  const [itemId, setItemId] = useState('');
  const [cantidad, setCantidad] = useState('1');
  const [lineas, setLineas] = useState<LineaSolicitud[]>([]);
  const [errores, setErrores] = useState<ErroresSolicitud>({});
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<Resultado>(null);
  const [enviando, setEnviando] = useState(false);
  const [guardada, setGuardada] = useState<Requerimiento | null>(null);

  const editable = !guardada || guardada.estado === 'BORRADOR';

  useEffect(() => {
    let vigente = true;
    setCargandoCatalogo(true);
    api
      .get<Item[]>('/catalogo/items', { categoria })
      .then((items) => {
        if (vigente) setCatalogo(items);
      })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
      })
      .finally(() => {
        if (vigente) setCargandoCatalogo(false);
      });
    return () => {
      vigente = false;
    };
  }, [categoria]);

  function agregar() {
    const item = catalogo.find((i) => i.id === itemId);
    const nuevos = validarLinea(item, cantidad, lineas, categoria);
    setErrores(nuevos);
    if (!item || !esValida(nuevos)) return;
    setLineas([...lineas, { item, cantidad: leerCantidad(cantidad) as number }]);
    setItemId('');
    setCantidad('1');
  }

  function quitar(id: string) {
    setLineas(lineas.filter((l) => l.item.id !== id));
    setErrores({});
  }

  /** Guarda (crea o actualiza) la solicitud en BORRADOR. Devuelve null si falló. */
  async function guardarBorrador(): Promise<Requerimiento | null> {
    const validacion = validarSolicitud(lineas);
    setErrores(validacion);
    if (!esValida(validacion)) return null;
    const cuerpo = aEntrada(lineas);
    const respuesta = guardada
      ? await api.put<Requerimiento>(`/requerimientos/${guardada.id}`, cuerpo)
      : await api.post<Requerimiento>('/requerimientos', cuerpo);
    setGuardada(respuesta);
    return respuesta;
  }

  async function ejecutar(accion: () => Promise<void>) {
    setError(null);
    setResultado(null);
    setEnviando(true);
    try {
      await accion();
    } catch (e) {
      if (e instanceof ErrorApi && e.codigo === 'REQUIERE_COLOGE') {
        setResultado({ tipo: 'aviso', texto: `${e.message} La solicitud quedó Registrada.` });
      } else if (e instanceof ErrorApi) {
        setError(e.message);
        if (e.estado === 422) {
          setErrores(Object.fromEntries(e.detalles.map((d) => [d.campo, d.mensaje])));
        }
      } else {
        setError(MENSAJE_GENERICO);
      }
    } finally {
      setEnviando(false);
    }
  }

  const guardar = () =>
    ejecutar(async () => {
      const req = await guardarBorrador();
      if (req) setResultado({ tipo: 'exito', texto: `Solicitud ${req.codigo} guardada.` });
    });

  const enviar = () =>
    ejecutar(async () => {
      const req = await guardarBorrador();
      if (!req) return;
      const enviada = await api.post<Requerimiento>(`/requerimientos/${req.id}/enviar`);
      // T103: se continúa en el detalle de la solicitud, con el mensaje de éxito.
      navegar(`/solicitudes/${enviada.id}`, {
        state: { exito: `Solicitud ${enviada.codigo} enviada por el conducto regular.` },
      });
    });

  const errorDeLinea = (indice: number) =>
    errores[`items.${indice}.cantidad`] ?? errores[`items.${indice}.item_id`];

  return (
    <main className="contenedor">
      <p>
        <Link to="/bandeja">← Volver a la bandeja</Link>
      </p>
      <Formulario
        titulo="Nueva solicitud"
        enviando={enviando || !editable}
        error={error}
        onEnviar={guardar}
      >
        <Campo id="categoria" etiqueta="Categoría">
          <select
            id="categoria"
            value={categoria}
            disabled={lineas.length > 0}
            onChange={(e) => {
              setCategoria(e.target.value as Categoria);
              setItemId('');
            }}
          >
            {CATEGORIAS.map((c) => (
              <option key={c.valor} value={c.valor}>
                {c.etiqueta}
              </option>
            ))}
          </select>
        </Campo>
        <Campo id="item" etiqueta="Ítem" error={errores.item}>
          <select
            id="item"
            value={itemId}
            onChange={(e) => setItemId(e.target.value)}
            aria-invalid={Boolean(errores.item)}
          >
            <option value="">{cargandoCatalogo ? 'Cargando catálogo…' : 'Elija un ítem'}</option>
            {catalogo.map((i) => (
              <option key={i.id} value={i.id}>
                {i.codigo} — {i.nombre} ({i.unidad_medida})
              </option>
            ))}
          </select>
        </Campo>
        <Campo id="cantidad" etiqueta="Cantidad" error={errores.cantidad}>
          <input
            id="cantidad"
            inputMode="numeric"
            value={cantidad}
            onChange={(e) => setCantidad(e.target.value)}
            aria-invalid={Boolean(errores.cantidad)}
          />
        </Campo>
        <div className="formulario__acciones">
          <button type="button" className="boton--secundario" onClick={agregar}>
            Agregar ítem
          </button>
        </div>

        <section className="lineas" aria-label="Ítems de la solicitud">
          <h3>Ítems ({lineas.length})</h3>
          {lineas.length === 0 ? <p>Todavía no agregó ítems.</p> : null}
          <ul>
            {lineas.map((l, indice) => (
              <li key={l.item.id} className="lineas__fila">
                <span>
                  {l.item.codigo} — {l.item.nombre}:{' '}
                  <strong>{cantidadConUnidad(l.cantidad, l.item.unidad_medida)}</strong>
                </span>
                <button
                  type="button"
                  className="boton--secundario"
                  onClick={() => quitar(l.item.id)}
                  aria-label={`Quitar ${l.item.nombre}`}
                >
                  Quitar
                </button>
                {errorDeLinea(indice) ? (
                  <p className="campo__error" role="alert">
                    {errorDeLinea(indice)}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
          {errores.items ? (
            <p className="campo__error" role="alert">
              {errores.items}
            </p>
          ) : null}
        </section>

        <div className="formulario__acciones">
          <button type="submit">{enviando ? 'Guardando…' : 'Guardar'}</button>
          <button type="button" onClick={enviar}>
            {enviando ? 'Enviando…' : 'Enviar'}
          </button>
        </div>
      </Formulario>

      {enviando ? <Cargando texto="Procesando la solicitud…" /> : null}
      {resultado ? <Mensaje tipo={resultado.tipo}>{resultado.texto}</Mensaje> : null}
      {guardada ? (
        <p>
          Estado actual: <EstadoEtiqueta estado={guardada.estado} />{' '}
          <Link to={`/solicitudes/${guardada.id}`}>Ver detalle</Link>
        </p>
      ) : null}
    </main>
  );
}
