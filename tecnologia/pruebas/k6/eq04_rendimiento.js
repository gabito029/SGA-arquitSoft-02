// EQ-04 (T091): rendimiento con 20 usuarios concurrentes durante 5 minutos.
// Estímulo y medidas de docs/ (constitución v1.2.0, desviación aprobada: k6 en lugar de Locust):
// p95 < 2 s y menos de 1 % de errores. Valida el listado, el detalle y el registro (US1, US5).
//   k6 run -e CONTRASENA=... --summary-export ../../evidencias/EQ-04/k6-resumen-001.json k6/eq04_rendimiento.js
import { sleep } from 'k6';
import { mezcla, preparar } from './comun.js';

export const options = {
  scenarios: {
    eq04: { executor: 'constant-vus', vus: 20, duration: '5m' },
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
