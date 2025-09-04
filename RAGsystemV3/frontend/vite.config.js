import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// 自定义插件：处理SPA路由fallback
function spaFallback() {
  return {
    name: 'spa-fallback',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // 如果是API请求，跳过
        if (req.url?.startsWith('/api')) {
          return next()
        }
        
        // 如果是静态资源（包括JS、CSS、图片等），跳过
        if (req.url?.includes('.') || req.url?.startsWith('/@') || req.url?.startsWith('/node_modules') || req.url?.startsWith('/images')) {
          return next()
        }
        
        // 其他所有请求都返回index.html
        req.url = '/index.html'
        next()
      })
    }
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), spaFallback()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://192.168.110.43:8000',
        changeOrigin: true,
        secure: false,
      },
      '/images': {
        target: 'http://192.168.110.43:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    port: 3000,
    host: '0.0.0.0',
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router'],
          element: ['element-plus', '@element-plus/icons-vue'],
        },
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "@/assets/styles/variables.scss";`,
      },
    },
  },
})
