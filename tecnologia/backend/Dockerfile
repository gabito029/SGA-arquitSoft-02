# API del SGA (FastAPI + uvicorn). ADR-011, C4 nivel 2.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Primero solo las dependencias, para aprovechar la caché de capas.
COPY pyproject.toml ./
RUN mkdir -p app seeds && touch app/__init__.py seeds/__init__.py \
    && pip install . \
    && rm -rf app seeds build *.egg-info

# Código, migraciones y seeds (alembic y "python -m seeds.cargar" se ejecutan desde /app).
COPY . .
RUN pip install --no-deps .

RUN useradd --create-home --uid 1000 sga
USER sga

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
