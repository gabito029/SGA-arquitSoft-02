// Cliente mínimo de la API REST: agrega el JWT, convierte los errores al esquema `Error` con
// mensajes en español y avisa del cierre de sesión ante un 401.
import { config } from '@/config';
import { mensajeDeError } from '../logica/mensajes';
import type { DetalleError, ErrorRespuesta } from './tipos';

/** Evento del navegador que escucha el contexto de sesión para cerrar la sesión. */
export const EVENTO_SESION_EXPIRADA = 'sga:sesion-expirada';

export class ErrorApi extends Error {
  readonly estado: number;
  readonly codigo: string;
  readonly detalles: DetalleError[];

  constructor(estado: number, codigo: string, mensaje: string, detalles: DetalleError[] = []) {
    super(mensaje);
    this.name = 'ErrorApi';
    this.estado = estado;
    this.codigo = codigo;
    this.detalles = detalles;
  }

  /** Mensaje del campo indicado, para mostrar los errores 422 junto a cada campo. */
  mensajeDeCampo(campo: string): string | undefined {
    return this.detalles.find((d) => d.campo === campo)?.mensaje;
  }
}

let tokenActual: string | null = null;

/** Lo llama el contexto de sesión al iniciar o cerrar la sesión. */
export function fijarToken(token: string | null): void {
  tokenActual = token;
}

export type Metodo = 'GET' | 'POST' | 'PUT';

export interface OpcionesSolicitud {
  metodo?: Metodo;
  cuerpo?: unknown;
  parametros?: Record<string, string | number | undefined>;
}

function construirUrl(ruta: string, parametros?: OpcionesSolicitud['parametros']): string {
  const consulta = Object.entries(parametros ?? {})
    .filter(([, valor]) => valor !== undefined && valor !== '')
    .map(([clave, valor]) => `${encodeURIComponent(clave)}=${encodeURIComponent(String(valor))}`)
    .join('&');
  return `${config.apiUrl}${ruta}${consulta ? `?${consulta}` : ''}`;
}

async function leerJson(respuesta: Response): Promise<unknown> {
  try {
    return await respuesta.json();
  } catch {
    return null;
  }
}

function esErrorRespuesta(valor: unknown): valor is ErrorRespuesta {
  return typeof valor === 'object' && valor !== null && 'codigo' in valor;
}

export async function solicitar<T>(ruta: string, opciones: OpcionesSolicitud = {}): Promise<T> {
  const cabeceras: Record<string, string> = { Accept: 'application/json' };
  if (opciones.cuerpo !== undefined) {
    cabeceras['Content-Type'] = 'application/json';
  }
  if (tokenActual) {
    cabeceras.Authorization = `Bearer ${tokenActual}`;
  }

  let respuesta: Response;
  try {
    respuesta = await fetch(construirUrl(ruta, opciones.parametros), {
      method: opciones.metodo ?? 'GET',
      headers: cabeceras,
      body: opciones.cuerpo !== undefined ? JSON.stringify(opciones.cuerpo) : undefined,
    });
  } catch {
    throw new ErrorApi(0, 'ERROR_RED', mensajeDeError(0));
  }

  if (respuesta.status === 204) {
    return undefined as T;
  }
  const cuerpo = await leerJson(respuesta);
  if (respuesta.ok) {
    return cuerpo as T;
  }

  if (respuesta.status === 401 && tokenActual) {
    // La sesión dejó de ser válida: el contexto de sesión la cierra y redirige al inicio.
    window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA));
  }
  const error = esErrorRespuesta(cuerpo) ? cuerpo : undefined;
  throw new ErrorApi(
    respuesta.status,
    error?.codigo ?? `HTTP_${respuesta.status}`,
    mensajeDeError(respuesta.status, error?.codigo, error?.mensaje),
    error?.detalles ?? [],
  );
}

export const api = {
  get: <T>(ruta: string, parametros?: OpcionesSolicitud['parametros']) =>
    solicitar<T>(ruta, { parametros }),
  post: <T>(ruta: string, cuerpo?: unknown) => solicitar<T>(ruta, { metodo: 'POST', cuerpo }),
  put: <T>(ruta: string, cuerpo?: unknown) => solicitar<T>(ruta, { metodo: 'PUT', cuerpo }),
};
