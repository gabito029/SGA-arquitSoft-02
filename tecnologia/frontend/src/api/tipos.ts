// Tipos de la API, tomados de specs/001-flujo-solicitud/contracts/openapi.yaml.

export type Rol =
  | 'OFICIAL_LOGISTICA'
  | 'COMANDANTE_UNIDAD'
  | 'JEFE_LOGISTICA_GU'
  | 'JEFE_ALMACEN'
  | 'ALMACENERO'
  | 'AUDITOR';

export type Categoria = 'INTENDENCIA' | 'MATERIAL_GUERRA';

export type EstadoRequerimiento =
  | 'BORRADOR'
  | 'PENDIENTE_VB_UNIDAD'
  | 'PENDIENTE_CONFORMIDAD'
  | 'PENDIENTE_AUTORIZACION_COLOGE'
  | 'PENDIENTE_APROBACION'
  | 'APROBADA'
  | 'RECHAZADA'
  | 'ANULADA'
  | 'EN_TRANSITO'
  | 'CONFIRMADA';

export type NivelFirma = 'VB_UNIDAD' | 'CONFORMIDAD_GU' | 'APROBACION_ALMACEN' | 'ACTA_RECEPCION';

export type AccionDisponible =
  | 'EDITAR'
  | 'ENVIAR'
  | 'ANULAR'
  | 'FIRMAR'
  | 'RECHAZAR'
  | 'DESPACHAR'
  | 'FIRMAR_ACTA';

export type ResultadoVerificacion = 'INTEGRA' | 'ALTERADA';

export interface DetalleError {
  campo: string;
  mensaje: string;
}

/** Esquema `Error` del contrato. */
export interface ErrorRespuesta {
  codigo: string;
  mensaje: string;
  detalles?: DetalleError[];
}

export interface OrganoResumen {
  id: string;
  codigo: string;
  nombre: string;
}

export interface Usuario {
  id: string;
  usuario: string;
  nombre_completo: string;
  rol: Rol;
  organo: OrganoResumen;
  almacen_id?: string | null;
}

export interface Token {
  access_token: string;
  token_type: 'bearer';
  /** Segundos. */
  expira_en: number;
  usuario: Usuario;
}

export interface Item {
  id: string;
  codigo: string;
  nombre: string;
  categoria: Categoria;
  unidad_medida: string;
  /** Decimal como texto, p. ej. "35.50". */
  valor_unitario: string;
}

export interface RequerimientoEntrada {
  categoria: Categoria;
  items: { item_id: string; cantidad: number }[];
}

export interface ItemRequerimiento {
  item: Item;
  cantidad_solicitada: number;
  cantidad_despachada?: number | null;
  cantidad_recibida?: number | null;
  observacion?: string | null;
}

export interface Requerimiento {
  id: string;
  codigo: string;
  estado: EstadoRequerimiento;
  categoria: Categoria;
  unidad: OrganoResumen;
  gran_unidad?: OrganoResumen;
  almacen?: OrganoResumen;
  monto_total?: string | null;
  items: ItemRequerimiento[];
  creado_en: string;
  actualizado_en?: string;
  acciones_disponibles: AccionDisponible[];
}

export interface PaginaRequerimientos {
  items: Requerimiento[];
  total: number;
  page: number;
  size: number;
}

export interface DecisionFirma {
  decision: 'APROBAR' | 'RECHAZAR';
  motivo?: string;
}

export interface Firma {
  id: string;
  nivel: NivelFirma;
  decision: 'APROBAR' | 'RECHAZAR';
  firmante: string;
  rol: Rol;
  organo: OrganoResumen;
  huella_sha256: string;
  metodo: string;
  firmado_en: string;
}

export interface Verificacion {
  requerimiento_id: string;
  resultado: ResultadoVerificacion;
  firmas: {
    firma_id: string;
    nivel: NivelFirma;
    resultado: ResultadoVerificacion;
    firmante: string;
    firmado_en: string;
  }[];
}

export interface EntradaHistorial {
  accion:
    | 'CREAR'
    | 'ENVIAR'
    | 'ENVIO_BLOQUEADO'
    | 'FIRMAR'
    | 'RECHAZAR'
    | 'ANULAR'
    | 'DESPACHAR'
    | 'FIRMAR_ACTA';
  estado_anterior?: EstadoRequerimiento | null;
  estado_nuevo: EstadoRequerimiento;
  usuario: string;
  rol: Rol;
  organo: OrganoResumen;
  motivo?: string | null;
  ocurrido_en: string;
}

export interface Stock {
  item: Item;
  cantidad: number;
}
