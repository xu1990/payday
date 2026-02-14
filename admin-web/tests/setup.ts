/*
 * Vitest 测试环境设置文件
 * 配置全局测试工具和 mock
 */

import { vi } from 'vitest'

// 全局 mock: Element Plus 消息组件
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
    },
    ElMessageBox: {
      confirm: vi.fn(),
      alert: vi.fn(),
      prompt: vi.fn(),
    },
  }
})

// 全局 mock: Vue Router
vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRoute: () => ({ path: '/', params: {}, query: {} }),
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      go: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
    }),
  }
})

// 全局 mock: Pinia stores
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: null,
    accessToken: '',
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshTokens: vi.fn(),
  }),
}))
