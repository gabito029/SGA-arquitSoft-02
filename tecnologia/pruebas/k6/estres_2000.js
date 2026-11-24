// Estrés progresivo hasta 2 000 usuarios (T093; constitución v1.2.0, principio VII).
// Escalones 50 → 200 → 500 → 1 000 → 2 000 VU. Se registran el p95, la tasa de errores y el punto de
// quiebre (el primer escalón donde se superan los umbrales; k6 marca el umbral como fallido y,
// con abortOnFail desactivado, la corrida continúa para medir todos los escalones).
// Solo se escribe en 001; se ejecuta en el incremento 002 (Sprint 2).
import { sleep } from 'k6';
import { mezcla, preparar } from './comun.js';

const ESCALONES = [50, 200, 500, 1000, 2000];

export const options = {
  scenarios: {
    estres: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: ESCALONES.flatMap((vus) => [
        { duration: '1m', target: vus }, // subida al escalón
        { duration: '2m', target: vus }, // meseta para medir
      ]).concat([{ duration: '1m', target: 0 }]),
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_duration: [{ threshold: 'p(95)<2000', abortOnFail: false }],
    http_req_failed: [{ threshold: 'rate<0.01', abortOnFail: false }],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

export function setup() {
  return preparar();
}

export default function (datos) {
  mezcla(datos);
  sleep(1);
}
