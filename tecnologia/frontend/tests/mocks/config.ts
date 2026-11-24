// Sustituto de src/config.ts en Jest: la misma configuración, sin import.meta.env.
import { leerConfig } from '../../src/leerConfig';

export const config = leerConfig({});
