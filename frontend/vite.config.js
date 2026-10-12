import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the Vite server proxies /api to the FastAPI backend on :8000.
// In containers Nginx (or the Kubernetes Ingress) does the same job.
export default defineConfig({
  plugins: [react()],
  build: {
    // Emit every asset (including small font subsets) as a file so the strict
    // Content-Security-Policy in nginx can stay at font-src 'self' without data: URIs.
    assetsInlineLimit: 0,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    css: false,
  },
})
