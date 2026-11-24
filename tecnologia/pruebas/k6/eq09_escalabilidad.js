// EQ-09 (T093): escalabilidad con 40 usuarios concurrentes y la misma mezcla que EQ-04.
// Solo se escribe en 001; se ejecuta en el incremento 002 (Sprint 2).
import { sleep } from 'k6';
import { mezcla, preparar } from './comun.js';

export const options = {
  scenarios: {
    eq09: { executor: 'constant-vus', vus: 40, duration: '5m' },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.01'],
  },
};

export function setup() {
  return preparar();
}

export default function (datos) {
  mezcla(datos);
  sleep(1);
}
