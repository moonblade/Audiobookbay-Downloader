import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/static/',
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: false,
    // Ensure assets are in the same directory for simpler serving
    assetsDir: 'assets',
  },
  server: {
    port: 3000,
    proxy: {
      '/search': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/add': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/list': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/torrent': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/title': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/role': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/login': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/logout': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/goodreads': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/goodreads-enabled': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/torrent-client-type': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/autoimport': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/selectCandidate': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
      '/change_password': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
    },
  },
})
