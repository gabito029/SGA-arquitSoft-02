#!/bin/sh
# Arranque del contenedor api: migraciones y seeds (ambos idempotentes) y luego el comando.
# CARGAR_SEEDS=false omite los datos de prueba ficticios (RC13).
set -e

echo "Aplicando migraciones (alembic upgrade head)..."
alembic upgrade head

if [ "${CARGAR_SEEDS:-true}" = "true" ]; then
    echo "Cargando datos de prueba (seeds)..."
    python -m seeds.cargar
fi

exec "$@"
