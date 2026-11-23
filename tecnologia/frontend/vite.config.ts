import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// En desarrollo, /api se reenvía a la API local (FastAPI en el puerto 8000).
// En Docker Compose lo hace Nginx (tecnologia/nginx/default.conf).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Única lectura de import.meta.env; Jest lo sustituye con el mismo alias (research §12).
      '@/config': fileURLToPath(new URL('./src/config.ts', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
