// Componentes base: mensajes, carga, etiqueta de estado y formulario.
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Cargando } from '../../src/componentes/Cargando';
import { EstadoEtiqueta } from '../../src/componentes/EstadoEtiqueta';
import { Campo, Formulario } from '../../src/componentes/Formulario';
import { Mensaje } from '../../src/componentes/Mensaje';

describe('componentes base', () => {
  it('Mensaje de error se anuncia como alerta; los demás como estado', () => {
    render(
      <>
        <Mensaje tipo="error">Falló</Mensaje>
        <Mensaje tipo="exito">Guardado</Mensaje>
      </>,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Error: Falló');
    expect(screen.getByRole('status')).toHaveTextContent('Listo: Guardado');
  });

  it('Cargando muestra su texto', () => {
    render(<Cargando texto="Enviando solicitud…" />);
    expect(screen.getByRole('status')).toHaveTextContent('Enviando solicitud…');
  });

  it('EstadoEtiqueta muestra la etiqueta de la interfaz', () => {
    render(<EstadoEtiqueta estado="EN_TRANSITO" />);
    expect(screen.getByText('Despachada')).toHaveClass('estado--en-curso');
  });

  it('Formulario evita el envío nativo, muestra el error y se desactiva mientras envía', async () => {
    const alEnviar = jest.fn();
    const { rerender } = render(
      <Formulario titulo="Nueva solicitud" error="Revise los datos" onEnviar={alEnviar}>
        <Campo id="cantidad" etiqueta="Cantidad" error="Debe ser mayor que 0.">
          <input id="cantidad" />
        </Campo>
        <button type="submit">Enviar</button>
      </Formulario>,
    );
    expect(screen.getByLabelText('Cantidad')).toBeInTheDocument();
    expect(screen.getByText('Debe ser mayor que 0.')).toBeInTheDocument();
    expect(screen.getByText(/Revise los datos/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(alEnviar).toHaveBeenCalledTimes(1);

    rerender(
      <Formulario titulo="Nueva solicitud" enviando onEnviar={alEnviar}>
        <button type="submit">Enviar</button>
      </Formulario>,
    );
    expect(screen.getByRole('button', { name: 'Enviar' })).toBeDisabled();
  });
});
