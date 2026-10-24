import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {                           // requests starting with /api ...
        target: 'http://localhost:3001',  // ... are forwarded to the backend
        changeOrigin: true,
      },
    },
  },
})
