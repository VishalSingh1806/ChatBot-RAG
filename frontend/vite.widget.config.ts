import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist-widget',
    lib: {
      entry: 'src/widget.tsx',
      name: 'ReCircleChatbot',
      formats: ['iife'],
      fileName: () => 'chatbot-widget.js'
    },
    rollupOptions: {
      output: {
        assetFileNames: 'chatbot-widget.[ext]',
        // Don't externalize anything - bundle everything
        inlineDynamicImports: true,
      }
    },
    // Ensure we're building for production
    minify: 'terser',
    sourcemap: false,
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  }
})
