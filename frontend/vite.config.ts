import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1', // 👈 Force Vite to use IPv4
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 👈 Also use IPv4 for proxy
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
