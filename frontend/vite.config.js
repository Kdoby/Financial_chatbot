import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat':    'http://localhost:8000',
      '/consult': 'http://localhost:8000',
      '/health':  'http://localhost:8000',
    }
  }
})

// 프로덕션에서는 VITE_API_URL 환경변수로 백엔드 URL 지정
