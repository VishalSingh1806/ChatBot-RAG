import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/session': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/query':   { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/collect_user_data': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/download_chat': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/trigger_contact_intent': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Create a single JS file for the widget
        entryFileNames: 'assets/chatbot-widget.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]'
      }
    }
  },
  define: {
    // Use production API URL when building
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'https://rebot.recircle.in')
  }
})
