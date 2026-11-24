import { leerConfig } from '../src/leerConfig';
import { config } from '@/config';

describe('leerConfig', () => {
  it('usa /api/v1 cuando no hay VITE_API_URL', () => {
    expect(leerConfig({}).apiUrl).toBe('/api/v1');
  });

  it('usa VITE_API_URL y quita la barra final', () => {
    expect(leerConfig({ VITE_API_URL: 'http://localhost:8000/api/v1/' }).apiUrl).toBe(
      'http://localhost:8000/api/v1',
    );
  });

  it('ignora un valor vacío o que no es texto', () => {
    expect(leerConfig({ VITE_API_URL: '   ' }).apiUrl).toBe('/api/v1');
    expect(leerConfig({ VITE_API_URL: true }).apiUrl).toBe('/api/v1');
  });

  it('en Jest, src/config se sustituye por la configuración por defecto', () => {
    expect(config.apiUrl).toBe('/api/v1');
  });
});
