// T018: documento oficial con encabezado, ítems y sellos digitales (002, FR-001 a FR-003).
import { render, screen, within } from '@testing-library/react';
import { DocumentoOficial } from '../../src/componentes/DocumentoOficial';
import { documento, SELLO_VB } from '../apoyo/documento';

describe('DocumentoOficial', () => {
  it('muestra el encabezado completo del requerimiento', () => {
    render(<DocumentoOficial documento={documento()} />);
    const doc = screen.getByRole('article', {
      name: /Requerimiento REQ-2026-000001/,
    });
    expect(doc).toHaveTextContent('SGA · Sistema de Gestión de Almacén con Firma Digital');
    expect(doc).toHaveTextContent('NúmeroREQ-2026-000001');
    expect(doc).toHaveTextContent('Unidad solicitanteBIM-11 · BIM N.° 11');
    expect(doc).toHaveTextContent('Gran Unidad1DE · 1.ª División de Ejército');
    expect(doc).toHaveTextContent('AlmacénSINTE · Almacén de intendencia');
    expect(doc).toHaveTextContent(/Fecha\d{2}\/\d{2}\/\d{4}/);
  });

  it('muestra la tabla de ítems', () => {
    render(<DocumentoOficial documento={documento()} />);
    const tabla = screen.getByRole('table', { name: 'Ítems' });
    const filas = within(tabla).getAllByRole('row');
    expect(filas).toHaveLength(2);
    expect(filas[1]).toHaveTextContent('INT-001Ración de campañaUND10');
  });

  it('muestra cada firma como sello con todos sus datos', () => {
    render(<DocumentoOficial documento={documento()} />);
    const sello = screen.getByText(/Aprobó: Comandante BIM-11/).closest('li');
    expect(sello).toHaveTextContent('Visto bueno de la unidad');
    expect(sello).toHaveTextContent('Comandante de la unidad · BIM-11 · BIM N.° 11');
    expect(sello).toHaveTextContent('Métodoed25519-sha256-v1');
    expect(sello).toHaveTextContent('12345678…abcdef90');
    expect(sello).toHaveTextContent(/Hora\d{2}:\d{2}/);
  });

  it('muestra el motivo de un rechazo', () => {
    const rechazo = {
      ...SELLO_VB,
      decision: 'RECHAZAR' as const,
      motivo: 'No corresponde',
    };
    render(<DocumentoOficial documento={documento({ sellos: [rechazo] })} />);
    expect(screen.getByText(/Rechazó: Comandante BIM-11/)).toBeInTheDocument();
    expect(screen.getByText('Motivo: No corresponde')).toBeInTheDocument();
  });

  it('indica cuando todavía no hay firmas', () => {
    render(<DocumentoOficial documento={documento({ sellos: [], pdf_disponible: false })} />);
    expect(screen.getByText('Todavía no hay firmas.')).toBeInTheDocument();
  });

  it('el acta muestra lo despachado, lo recibido, la observación y las diferencias', () => {
    const acta = documento({
      tipo: 'ACTA',
      tiene_diferencias: true,
      items: [
        {
          codigo: 'INT-001',
          descripcion: 'Ración de campaña',
          unidad_medida: 'UND',
          categoria: 'INTENDENCIA',
          cantidad_solicitada: 10,
          cantidad_despachada: 10,
          cantidad_recibida: 9,
          observacion: 'Falta 1',
        },
      ],
      sellos: [{ ...SELLO_VB, nivel: 'ACTA_RECEPCION', rol: 'OFICIAL_LOGISTICA' }],
    });
    render(<DocumentoOficial documento={acta} />);
    expect(screen.getByRole('article', { name: /Acta de recepción/ })).toBeInTheDocument();
    expect(screen.getAllByRole('row')[1]).toHaveTextContent(
      'INT-001Ración de campañaUND10109Falta 1',
    );
    expect(screen.getByText(/Se registraron diferencias/)).toBeInTheDocument();
  });

  it('el acta sin diferencias lo indica', () => {
    render(<DocumentoOficial documento={documento({ tipo: 'ACTA', tiene_diferencias: false })} />);
    expect(screen.getByText('Lo recibido coincide con lo despachado.')).toBeInTheDocument();
  });
});
