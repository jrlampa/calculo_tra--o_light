import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    include: ['src/test/**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: [
      'node_modules/',
      'e2e/',
      '**/*.d.ts',
      '**/*.config.*',
      'coverage/',
      'dist/',
      'build/',
      'public/'
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'coverage/',
        'dist/',
        'build/',
        'public/',
        'e2e/'
      ],
      thresholds: {
        global: {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85
        }
      }
    },
    globals: true
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
