import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'
import { parseEnv } from './src/shared/api/env'

export default defineConfig(({ mode }) => {
  // Fail fast (dev server and build) when the API base URL is missing or invalid.
  // The test run provides its own value through `test.env` below.
  if (mode !== 'test') {
    parseEnv(loadEnv(mode, process.cwd(), 'VITE_'))
  }

  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path: string) => path.replace(/^\/api/, ''),
        },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./test/setup.ts'],
      env: { VITE_API_BASE_URL: 'http://api.test' },
      coverage: {
        provider: 'v8',
        include: ['src/**/*.{ts,tsx}'],
        exclude: ['src/main.tsx', 'src/vite-env.d.ts'],
        reporter: ['text', 'lcov'],
        thresholds: { lines: 80, statements: 80, functions: 80, branches: 80 },
      },
    },
  }
})
