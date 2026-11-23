// Mensajes en español para los errores de la API: por `codigo` del contrato y por código HTTP.

export const MENSAJES_POR_CODIGO: Record<string, string> = {
  TRANSICION_NO_PERMITIDA: 'La solicitud ya no está en un estado que permita esta acción.',
  NIVEL_YA_FIRMADO: 'Este nivel ya firmó la solicitud.',
  REQUIERE_COLOGE: 'Requiere autorización del COLOGE (disponible en un próximo incremento).',
  STOCK_INSUFICIENTE: 'No hay stock suficiente en el almacén para despachar estas cantidades.',
  ESTADO_CAMBIADO:
    'Otra persona actuó sobre esta solicitud al mismo tiempo. Recargue la página e intente de nuevo.',
};

export const MENSAJES_POR_ESTADO_HTTP: Record<number, string> = {
  0: 'No se pudo conectar con el servidor. Revise su conexión e intente de nuevo.',
  401: 'Su sesión no es válida o expiró. Inicie sesión de nuevo.',
  403: 'Su rol no permite realizar esta acción.',
  404: 'La solicitud no existe o no pertenece a su jurisdicción.',
  409: 'La acción entra en conflicto con el estado actual de la solicitud.',
  422: 'Revise los datos ingresados.',
  500: 'Ocurrió un error inesperado en el servidor. Intente de nuevo.',
};

export const MENSAJE_GENERICO = 'No se pudo completar la operación. Intente de nuevo.';

/**
 * Elige el mensaje que verá el usuario. Prioridad: mensaje propio del `codigo` de negocio,
 * luego el mensaje en español que envía la API y, si no hay, el del código HTTP.
 */
export function mensajeDeError(estado: number, codigo?: string, mensajeServidor?: string): string {
  if (codigo && MENSAJES_POR_CODIGO[codigo]) {
    return MENSAJES_POR_CODIGO[codigo];
  }
  if (mensajeServidor && mensajeServidor.trim() !== '') {
    return mensajeServidor;
  }
  return MENSAJES_POR_ESTADO_HTTP[estado] ?? MENSAJE_GENERICO;
}
