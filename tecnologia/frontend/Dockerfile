# Interfaz web del SGA: build con Vite y servida por Nginx (ADR-012, C4 nivel 2).
# El contexto de build es tecnologia/ (ver docker-compose.yml), para incluir nginx/default.conf.

FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
