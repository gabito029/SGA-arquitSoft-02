// Revisión del documento antes de firmar o rechazar (incremento 002, US2: FR-005 y FR-006). El
// firmante ve el documento completo dentro del diálogo y marca "He revisado el documento"; hasta
// entonces el botón de confirmar queda desactivado. La casilla aparece solo cuando el documento ya
// cargó: sin documento no hay nada que revisar.
import { useEffect, useState } from 'react';
import { ErrorApi } from '../api/cliente';
import { obtenerDocumento } from '../api/documentos';
import type { Documento } from '../api/tipos';
import { MENSAJE_GENERICO } from '../logica/mensajes';
import { Cargando } from './Cargando';
import { DocumentoOficial } from './DocumentoOficial';
import { Mensaje } from './Mensaje';

export const TEXTO_REVISION = 'He revisado el documento';

interface PropsCasilla {
  marcada: boolean;
  onCambiar: (marcada: boolean) => void;
}

export function CasillaRevision({ marcada, onCambiar }: PropsCasilla) {
  return (
    <label className="revision">
      <input type="checkbox" checked={marcada} onChange={(e) => onCambiar(e.target.checked)} />
      {TEXTO_REVISION}
    </label>
  );
}

interface PropsRevision {
  requerimientoId: string;
  revisado: boolean;
  onCambiar: (revisado: boolean) => void;
}

/** Carga el documento, lo muestra dentro del diálogo y ofrece la casilla de revisión. */
export function RevisionDocumento({ requerimientoId, revisado, onCambiar }: PropsRevision) {
  const [documento, setDocumento] = useState<Documento | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    obtenerDocumento(requerimientoId)
      .then((d) => {
        if (vigente) setDocumento(d);
      })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : MENSAJE_GENERICO);
      });
    return () => {
      vigente = false;
    };
  }, [requerimientoId]);

  if (error) return <Mensaje tipo="error">{error}</Mensaje>;
  if (!documento) return <Cargando />;
  return (
    <>
      <div className="dialogo__documento" tabIndex={0} aria-label="Documento a revisar">
        <DocumentoOficial documento={documento} />
      </div>
      <CasillaRevision marcada={revisado} onCambiar={onCambiar} />
    </>
  );
}
