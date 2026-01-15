import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  build: {
    outDir: path.resolve(__dirname, '../dist_web')
  },
  server: {
    host: true, // 开启局域网访问
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        rewrite: (path) => path  // 保持 api 前缀
      },
      '/home': {
        target: 'http://117.50.163.168:80',
        changeOrigin: true,
        rewrite: (path) => path  // 保持 api 前缀
      }
    }
  }
})
