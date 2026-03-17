import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const hmrHabilitado = process.env.DISABLE_HMR !== 'true';
  const hostHmr = process.env.VITE_HMR_HOST || '127.0.0.1';
  const portaHmr = Number(process.env.VITE_HMR_PORT || 24678);

  return {
    plugins: [react(), tailwindcss()],
    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // Permite que o servidor integrado escolha uma porta livre para o WebSocket do HMR.
      hmr: hmrHabilitado
        ? {
            host: hostHmr,
            port: portaHmr,
            clientPort: portaHmr,
          }
        : false,
    },
  };
});
