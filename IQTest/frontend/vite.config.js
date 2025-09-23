import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Configuración dinámica para soportar despliegue bajo subruta (/iqtest/) en producción.
// Usa variables en .env (.env.development / .env.production):
//  VITE_BASE_PATH -> Ej: / (dev) o /iqtest/ (prod)
//  VITE_API_BASE -> Ej: /api (dev, proxied) o /iqtest/api (prod)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const basePath = env.VITE_BASE_PATH || '/';
  return {
    base: basePath, // Asegura que los assets se generen con la ruta correcta
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      emptyOutDir: true
    }
  };
});