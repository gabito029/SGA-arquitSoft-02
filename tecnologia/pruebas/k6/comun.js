// Funciones compartidas por los scripts de k6 del SGA (research §11).
// La contraseña llega por la variable de entorno CONTRASENA (nunca se versiona):
//   k6 run -e CONTRASENA=... -e BASE_URL=http://localhost:8080 k6/eq04_rendimiento.js
import http from 'k6/http';
import { check, fail } from 'k6';

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API = `${BASE_URL}/api/v1`;

export function iniciarSesion(usuario) {
  if (!__ENV.CONTRASENA) fail('Defina la variable CONTRASENA (la de CONTRASENA_DEMO del .env).');
  const respuesta = http.post(
    `${API}/auth/login`,
    JSON.stringify({ usuario, contrasena: __ENV.CONTRASENA }),
    { headers: { 'Content-Type': 'application/json' }, tags: { nombre: 'login' } },
  );
  if (!check(respuesta, { 'login 200': (r) => r.status === 200 })) {
    fail(`No se pudo iniciar sesión con ${usuario}: ${respuesta.status}`);
  }
  return respuesta.json('access_token');
}

/** Prepara el escenario: token del oficial, ítems de intendencia y una solicitud para el detalle. */
export function preparar() {
  const token = iniciarSesion('oficial.bim11');
  const cabeceras = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  const items = http
    .get(`${API}/catalogo/items?categoria=INTENDENCIA`, { headers: cabeceras })
    .json()
    .map((i) => i.id);
  const creada = http.post(
    `${API}/requerimientos`,
    JSON.stringify({ items: [{ item_id: items[0], cantidad: 1 }] }),
    { headers: cabeceras },
  );
  return { cabeceras, items, requerimientoId: creada.json('id') };
}

/**
 * Mezcla de EQ-04/EQ-09: 60 % bandeja, 30 % detalle y 10 % registro. `etiquetas` se agrega a cada
 * petición (por ejemplo, el escalón de la prueba de estrés).
 */
export function mezcla(datos, etiquetas = {}) {
  const opciones = { headers: datos.cabeceras };
  const azar = Math.random();
  if (azar < 0.6) {
    const r = http.get(`${API}/requerimientos?page=1&size=20`, {
      ...opciones,
      tags: { nombre: 'bandeja', ...etiquetas },
    });
    check(r, { 'bandeja 200': (x) => x.status === 200 });
  } else if (azar < 0.9) {
    const r = http.get(`${API}/requerimientos/${datos.requerimientoId}`, {
      ...opciones,
      tags: { nombre: 'detalle', ...etiquetas },
    });
    check(r, { 'detalle 200': (x) => x.status === 200 });
  } else {
    const item = datos.items[Math.floor(Math.random() * datos.items.length)];
    const r = http.post(
      `${API}/requerimientos`,
      JSON.stringify({ items: [{ item_id: item, cantidad: 1 }] }),
      { ...opciones, tags: { nombre: 'registro', ...etiquetas } },
    );
    check(r, { 'registro 201': (x) => x.status === 201 });
  }
}
