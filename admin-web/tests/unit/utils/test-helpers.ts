/**
 * Admin-web 测试辅助工具
 */
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

/**
 * Mock Element Plus 组件
 */
export function mockElementPlus() {
  return {
    ElButton: {
      name: 'ElButton',
      template: '<button @click="$emit(\'click\')"><slot /></button>',
    },
    ElTable: {
      name: 'ElTable',
      template: '<table><slot /></table>',
    },
    ElTag: {
      name: 'ElTag',
      template: '<span :class="type"><slot /></span>',
    },
    ElDialog: {
      name: 'ElDialog',
      template: '<div v-if="modelValue"><slot /></div>',
    },
    ElInput: {
      name: 'ElInput',
      template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    },
    ElForm: {
      name: 'ElForm',
      template: '<form><slot /></form>',
    },
  }
}

/**
 * 全局测试配置
 */
export function setupGlobalTestConfig() {
  config.global.stubs = {
    ...mockElementPlus(),
  }

  // Mock Element Plus 组件
  config.global.components = {
    ...mockElementPlus(),
  }
}

/**
 * Mock Pinia store
 */
export function createMockStore<T extends Record<string, any>>(defaults: T) {
  return {
    ...defaults,
    $reset: vi.fn(function() {
      Object.assign(this, defaults)
    }),
    $patch: vi.fn(function(partial: Partial<T>) {
      Object.assign(this, partial)
    }),
  }
}

/**
 * Mock Vue Router
 */
export function mockVueRouter() {
  const push = vi.fn()
  const replace = vi.fn()
  const go = vi.fn()
  const back = vi.fn()
  const forward = vi.fn()

  return {
    push,
    replace,
    go,
    back,
    forward,
    currentRoute: {
      value: {
        path: '/',
        name: 'home',
        params: {},
        query: {},
      },
    },
   路由: {
      path: '/',
      name: 'home',
    },
  }
}

/**
 * 创建模拟的 HTTP 客户端
 */
export function createMockHttpClient() {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  }
}

/**
 * Mock API 响应
 */
export function mockApiResponse<T>(data: T, delay = 100): Promise<{ data: T }> {
  return new Promise(resolve => {
    setTimeout(() => resolve({ data }), delay)
  })
}

/**
 * Mock API 错误
 */
export function mockApiError(
  message: string,
  code = 500,
  delay = 100
): Promise<never> {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject(new Error(message))
    }, delay)
  })
}

/**
 * 延迟函数
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 等待条件满足
 */
export async function waitFor(
  condition: () => boolean,
  options: { timeout?: number; interval?: number } = {}
): Promise<void> {
  const { timeout = 5000, interval = 50 } = options
  const startTime = Date.now()

  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error(`条件在 ${timeout}ms 内未满足`)
    }
    await delay(interval)
  }
}

/**
 * 生成随机字符串
 */
export function randomString(length = 10): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 生成随机数字
 */
export function randomNumber(min = 0, max = 100): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

/**
 * 创建测试用的用户数据
 */
export function createTestUser(overrides = {}) {
  return {
    id: randomString(20),
    username: `test_user_${randomString(5)}`,
    nickname: `测试用户${randomNumber(1000, 9999)}`,
    role: 'user',
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * 创建测试用的订单数据
 */
export function createTestOrder(overrides = {}) {
  return {
    id: randomString(20),
    order_id: `TEST_ORDER_${randomNumber(100000, 999999)}`,
    amount: randomNumber(1000, 99999),
    status: 'pending',
    payment_method: 'wechat',
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * 创建测试用的帖子数据
 */
export function createTestPost(overrides = {}) {
  return {
    id: randomString(20),
    content: `测试内容 ${randomString(20)}`,
    mood: 'happy',
    is_anonymous: false,
    risk_status: 'passed',
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * 格式化日期为测试友好的格式
 */
export function formatDateForTest(date: Date): string {
  return date.toISOString().split('T')[0]
}

/**
 * 格式化日期时间为测试友好的格式
 */
export function formatDateTimeForTest(date: Date): string {
  return date.toISOString()
}

/**
 * 断言响应数据结构
 */
export function assertResponseShape(
  response: Record<string, any>,
  requiredKeys: string[]
) {
  requiredKeys.forEach(key => {
    expect(response).toHaveProperty(key)
  })
}

/**
 * 断言组件渲染
 */
export function assertComponentRendered(wrapper: any, selector: string) {
  expect(wrapper.find(selector).exists()).toBe(true)
}

/**
 * 断言组件未渲染
 */
export function assertComponentNotRendered(wrapper: any, selector: string) {
  expect(wrapper.find(selector).exists()).toBe(false)
}

/**
 * 断言事件触发
 */
export function assertEventEmitted(wrapper: any, eventName: string, count = 1) {
  expect(wrapper.emitted(eventName)).toBeTruthy()
  if (count !== null) {
    expect(wrapper.emitted(eventName).length).toBe(count)
  }
}

/**
 * 清除所有 mocks
 */
export function clearAllMocks() {
  vi.clearAllMocks()
}

/**
 * 深度克隆对象
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}
