import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/session': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/query':   { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/collect_user_data': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
