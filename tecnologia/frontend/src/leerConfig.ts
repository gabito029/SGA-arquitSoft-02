// Construye la configuración del frontend a partir de un conjunto de variables de entorno.
// Es una función pura: así se prueba con Jest sin depender de import.meta.env (research §12).

export interface Config {
  /** URL base de la API REST, sin barra final. */
  apiUrl: string;
}

export type VariablesEntorno = Record<string, string | boolean | undefined>;

const API_URL_POR_DEFECTO = '/api/v1';

export function leerConfig(entorno: VariablesEntorno): Config {
  const valor = entorno.VITE_API_URL;
  const apiUrl = typeof valor === 'string' && valor.trim() !== '' ? valor.trim() : API_URL_POR_DEFECTO;
  return { apiUrl: apiUrl.replace(/\/+$/, '') };
}
