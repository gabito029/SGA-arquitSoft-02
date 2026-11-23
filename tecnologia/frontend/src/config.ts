// Única lectura de import.meta.env en todo el frontend (research §12).
// En Jest este módulo se sustituye con moduleNameMapper (tests/mocks/config.ts).
import { leerConfig } from './leerConfig';

export const config = leerConfig(import.meta.env);
