// Estrés progresivo hasta 2 000 usuarios (T093; constitución v1.2.0, principio VII).
// Escalones 50 → 200 → 500 → 1 000 → 2 000 VU: 1 min de subida y 2 min de meseta por escalón.
// Cada petición lleva la etiqueta `escalon` (según el tiempo transcurrido), y el resumen trae el
// p95, la tasa de errores y las peticiones de cada escalón: el punto de quiebre es el primer
// escalón que supera los umbrales. abortOnFail está desactivado para medir todos los escalones.
//   k6 run -e CONTRASENA=... --summary-export ../../evidencias/ESTRES/k6-estres-2000.json k6/estres_2000.js
import exec from 'k6/execution';
import { sleep } from 'k6';
import { mezcla, preparar } from './comun.js';

const ESCALONES = [50, 200, 500, 1000, 2000];
const SUBIDA_S = 60;
const MESETA_S = 120;

const umbralesPorEscalon = {};
for (const vus of ESCALONES) {
  umbralesPorEscalon[`http_req_duration{escalon:${vus}}`] = [
    { threshold: 'p(95)<2000', abortOnFail: false },
  ];
  umbralesPorEscalon[`http_req_failed{escalon:${vus}}`] = [
    { threshold: 'rate<0.01', abortOnFail: false },
  ];
  umbralesPorEscalon[`http_reqs{escalon:${vus}}`] = ['count>=0'];
}

export const options = {
  scenarios: {
    estres: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: ESCALONES.flatMap((vus) => [
        { duration: `${SUBIDA_S}s`, target: vus },
        { duration: `${MESETA_S}s`, target: vus },
      ]).concat([{ duration: '1m', target: 0 }]),
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_duration: [{ threshold: 'p(95)<2000', abortOnFail: false }],
    http_req_failed: [{ threshold: 'rate<0.01', abortOnFail: false }],
    ...umbralesPorEscalon,
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

/** Escalón al que pertenece el instante actual (la subida cuenta para el escalón al que va). */
function escalonActual() {
  const segundos = exec.instance.currentTestRunDuration / 1000;
  const indice = Math.min(Math.floor(segundos / (SUBIDA_S + MESETA_S)), ESCALONES.length - 1);
  return String(ESCALONES[indice]);
}

export function setup() {
  return preparar();
}

export default function (datos) {
  mezcla(datos, { escalon: escalonActual() });
  sleep(1);
}
