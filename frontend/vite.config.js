import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/sessions': 'http://localhost:8000',
      '/tool-sets': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000'
    }
  }
})
