import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/ExcelConverter/',
  server: {
    port: 5174
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
