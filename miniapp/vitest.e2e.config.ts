/**
 * Vitest E2E 测试配置
 * 用于运行端到端测试
 */
import { defineConfig } from 'vitest/config'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  test: {
    globals: true,
    // E2E 测试需要在真实环境中运行，不使用 mock 环境
    environment: 'node',
    include: ['tests/e2e/e2e-all.test.ts'],
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache',
      'tests/unit',
    ],
    // E2E 测试通常不需要覆盖率报告
    coverage: { enabled: false },
    // E2E 测试超时时间设置更长
    testTimeout: 120000,
    hookTimeout: 180000,
    // 使用单线程池确保所有测试在同一个进程中运行
    poolOptions: {
      threads: {
        singleThread: true,
      },
      forks: {
        singleFork: true,
      },
    },
    // 监听模式配置
    watch: false,
    // 显示完整错误堆栈
    reporters: ['verbose'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
