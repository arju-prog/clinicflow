import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In dev (`npm run dev`), proxy API calls to a locally running FastAPI on :8000.
// In Docker/Kubernetes, Nginx and the Ingress do this routing instead.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'node',
  },
});
