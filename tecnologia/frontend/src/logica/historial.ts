// Etiquetas de la línea de tiempo (FR-028): qué pasó y con qué rol.
import type { EntradaHistorial, Rol } from '../api/tipos';

export const ETIQUETAS_ACCION_HISTORIAL: Record<EntradaHistorial['accion'], string> = {
  CREAR: 'Registró la solicitud',
  ENVIAR: 'Envió la solicitud',
  ENVIO_BLOQUEADO: 'Envío bloqueado',
  FIRMAR: 'Firmó',
  RECHAZAR: 'Rechazó',
  ANULAR: 'Anuló',
  DESPACHAR: 'Despachó',
  FIRMAR_ACTA: 'Firmó el acta de recepción',
};

export const ETIQUETAS_ROL: Record<Rol, string> = {
  OFICIAL_LOGISTICA: 'Oficial de logística',
  COMANDANTE_UNIDAD: 'Comandante de la unidad',
  JEFE_LOGISTICA_GU: 'Jefe de logística de la División/Brigada',
  JEFE_ALMACEN: 'Jefe de almacén',
  ALMACENERO: 'Almacenero',
  AUDITOR: 'Auditor',
};

/** Entradas en orden cronológico (la API ya las ordena; se asegura por si acaso). */
export function ordenarHistorial(entradas: EntradaHistorial[]): EntradaHistorial[] {
  return [...entradas].sort((a, b) => a.ocurrido_en.localeCompare(b.ocurrido_en));
}
