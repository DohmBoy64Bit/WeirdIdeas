import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy API and WebSocket calls to backend running on localhost:8000
export default defineConfig({
  plugins: [react({
    include: '**/*.{jsx,js}',
  })],
  server: {
    proxy: {
      '/lobbies': { target: 'http://localhost:8000', changeOrigin: true },
      '/auth': { target: 'http://localhost:8000', changeOrigin: true },
      '/categories': { target: 'http://localhost:8000', changeOrigin: true },
      '/data': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true }
    }
  }
})