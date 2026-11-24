// T082: la línea de tiempo muestra las entradas en orden, con sus etiquetas y el motivo.
import { render, screen, within } from '@testing-library/react';
import type { EntradaHistorial } from '../../src/api/tipos';
import { LineaTiempo } from '../../src/componentes/LineaTiempo';

const BIM11 = { id: 'u1', codigo: 'BIM-11', nombre: 'BIM N.° 11' };

const ENTRADAS: EntradaHistorial[] = [
  {
    accion: 'FIRMAR',
    estado_anterior: 'PENDIENTE_VB_UNIDAD',
    estado_nuevo: 'PENDIENTE_CONFORMIDAD',
    usuario: 'Comandante BIM-11',
    rol: 'COMANDANTE_UNIDAD',
    organo: BIM11,
    ocurrido_en: '2026-11-24T10:05:00Z',
  },
  {
    accion: 'CREAR',
    estado_anterior: null,
    estado_nuevo: 'BORRADOR',
    usuario: 'Oficial de logística BIM-11',
    rol: 'OFICIAL_LOGISTICA',
    organo: BIM11,
    ocurrido_en: '2026-11-24T10:00:00Z',
  },
  {
    accion: 'RECHAZAR',
    estado_anterior: 'PENDIENTE_CONFORMIDAD',
    estado_nuevo: 'RECHAZADA',
    usuario: 'Jefe de logística 1.ª DE',
    rol: 'JEFE_LOGISTICA_GU',
    organo: { id: 'g1', codigo: '1DE', nombre: '1.ª División de Ejército' },
    motivo: 'No corresponde a la dotación',
    ocurrido_en: '2026-11-24T11:00:00Z',
  },
];

describe('LineaTiempo', () => {
  it('muestra las entradas en orden cronológico con sus etiquetas', () => {
    render(<LineaTiempo entradas={ENTRADAS} />);
    const pasos = within(screen.getByRole('list', { name: 'Línea de tiempo' })).getAllByRole(
      'listitem',
    );
    expect(pasos).toHaveLength(3);
    expect(pasos[0]).toHaveTextContent('Registró la solicitud');
    expect(pasos[0]).toHaveTextContent('Oficial de logística BIM-11 · Oficial de logística · BIM-11');
    expect(pasos[0]).toHaveTextContent('Registrada');
    expect(pasos[1]).toHaveTextContent('Firmó');
    expect(pasos[1]).toHaveTextContent(
      'En visto bueno de la unidad → En conformidad de la División/Brigada',
    );
    expect(pasos[2]).toHaveTextContent('Rechazó');
    expect(pasos[2]).toHaveTextContent('1DE');
  });

  it('cada paso lleva un ícono con el tono del estado al que llegó (T111)', () => {
    render(<LineaTiempo entradas={ENTRADAS} />);
    const pasos = within(screen.getByRole('list', { name: 'Línea de tiempo' })).getAllByRole(
      'listitem',
    );
    const iconos = pasos.map((p) => p.querySelector('.linea-tiempo__icono'));
    iconos.forEach((i) => expect(i?.querySelector('svg')).toHaveAttribute('aria-hidden', 'true'));
    expect(iconos[0]).toHaveClass('linea-tiempo__icono--neutral');
    expect(iconos[1]).toHaveClass('linea-tiempo__icono--pendiente');
    expect(iconos[2]).toHaveClass('linea-tiempo__icono--rechazada');
  });

  it('muestra el motivo solo cuando existe', () => {
    render(<LineaTiempo entradas={ENTRADAS} />);
    expect(screen.getAllByText(/^Motivo:/)).toHaveLength(1);
    expect(screen.getByText('Motivo: No corresponde a la dotación')).toBeInTheDocument();
  });

  it('indica cuando no hay movimientos', () => {
    render(<LineaTiempo entradas={[]} />);
    expect(screen.getByText('La solicitud todavía no tiene movimientos.')).toBeInTheDocument();
  });
});
