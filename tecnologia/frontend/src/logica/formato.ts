// Formatos de la interfaz (T104): montos en soles con formato es-PE y unidades en plural.
// Se arman a mano para que el resultado no dependa de los datos regionales del navegador:
// separador de miles con espacio (no separable) y coma decimal, por ejemplo "S/ 1 255,00".

const ESPACIO = '\u00a0';

/** "1255.5" → "S/ 1 255,50". Acepta el decimal como texto (como lo envía la API) o número. */
export function formatoSoles(monto: string | number): string {
  const valor = typeof monto === 'number' ? monto : Number(monto);
  if (!Number.isFinite(valor)) return `S/${ESPACIO}${monto}`;
  const [entero, decimales] = Math.abs(valor).toFixed(2).split('.');
  const conMiles = entero.replace(/\B(?=(\d{3})+(?!\d))/g, ESPACIO);
  return `${valor < 0 ? '-' : ''}S/${ESPACIO}${conMiles},${decimales}`;
}

const SIN_TILDE: Record<string, string> = { á: 'a', é: 'e', í: 'i', ó: 'o', ú: 'u' };

/** Plural de una palabra en español: vocal → +s; -z → -ces; consonante → +es (sin la tilde aguda). */
function pluralPalabra(palabra: string): string {
  if (/[aeiouáéíóú]$/i.test(palabra)) return `${palabra}s`;
  if (/z$/i.test(palabra)) return `${palabra.slice(0, -1)}ces`;
  // "bidón" → "bidones", "camión" → "camiones": la tilde de la última sílaba desaparece.
  const sinTilde = palabra.replace(/([áéíóú])([a-zñ]*)$/i, (_, v: string, resto: string) =>
    (SIN_TILDE[v.toLowerCase()] ?? v) + resto,
  );
  return `${sinTilde}es`;
}

/** Unidad de medida según la cantidad: 1 unidad, 2 unidades, 3 pares, 2 bidones. */
export function unidadMedida(unidad: string, cantidad: number): string {
  if (cantidad === 1 || unidad.trim() === '') return unidad;
  const [primera, ...resto] = unidad.split(' ');
  // Solo la primera palabra cambia: "saco de 50 kg" → "sacos de 50 kg".
  return [pluralPalabra(primera), ...resto].join(' ');
}

/** "4 unidades", "1 par". */
export function cantidadConUnidad(cantidad: number, unidad: string): string {
  return `${cantidad} ${unidadMedida(unidad, cantidad)}`;
}

/** Fecha corta es-PE: "24/11/2026". */
export function fechaCorta(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return '';
  const dd = String(fecha.getDate()).padStart(2, '0');
  const mm = String(fecha.getMonth() + 1).padStart(2, '0');
  return `${dd}/${mm}/${fecha.getFullYear()}`;
}
