import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        manualChunks: {
          'd3-vendor': ['d3'],
          'recharts-vendor': ['recharts'],
          'pdf-vendor': ['jspdf'],
          'react-vendor': ['react', 'react-dom'],
        }
      }
    }
  },
  server: {
    port: 5173,
  }
})
