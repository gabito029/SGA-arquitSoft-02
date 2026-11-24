// T100: confirmación propia de la página, accesible y sin window.confirm.
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DialogoConfirmacion } from '../../src/componentes/DialogoConfirmacion';

function renderizar(enviando = false) {
  const onConfirmar = jest.fn();
  const onCancelar = jest.fn();
  render(
    <DialogoConfirmacion
      titulo="¿Firmar?"
      advertencia="No se puede deshacer."
      confirmar="Sí, firmar"
      enviando={enviando}
      onConfirmar={onConfirmar}
      onCancelar={onCancelar}
    >
      <p>Detalle de la acción</p>
    </DialogoConfirmacion>,
  );
  return { onConfirmar, onCancelar };
}

describe('DialogoConfirmacion', () => {
  it('es un alertdialog con título, detalle y advertencia, y recibe el foco', () => {
    renderizar();
    const dialogo = screen.getByRole('alertdialog', { name: '¿Firmar?' });
    expect(dialogo).toHaveAccessibleDescription('No se puede deshacer.');
    expect(dialogo).toHaveTextContent('Detalle de la acción');
    expect(dialogo).toHaveFocus();
  });

  it('confirma, cancela y cierra con Escape', async () => {
    const usuario = userEvent.setup();
    const { onConfirmar, onCancelar } = renderizar();
    await usuario.click(screen.getByRole('button', { name: 'Sí, firmar' }));
    expect(onConfirmar).toHaveBeenCalledTimes(1);
    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }));
    await usuario.keyboard('{Escape}');
    expect(onCancelar).toHaveBeenCalledTimes(2);
  });

  it('mientras procesa desactiva los botones e ignora Escape', async () => {
    const usuario = userEvent.setup();
    const { onCancelar } = renderizar(true);
    expect(screen.getByRole('button', { name: 'Procesando…' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled();
    screen.getByRole('alertdialog').focus();
    await usuario.keyboard('{Escape}');
    expect(onCancelar).not.toHaveBeenCalled();
  });
});
