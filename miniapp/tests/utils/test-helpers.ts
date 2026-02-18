/**
 * Miniapp 测试辅助工具
 */
import { vi } from 'vitest'

/**
 * Mock uni API
 */
export function mockUniApi() {
  return {
    navigateTo: vi.fn(),
    navigateBack: vi.fn(),
    redirectTo: vi.fn(),
    reLaunch: vi.fn(),
    switchTab: vi.fn(),
    getSystemInfoSync: vi.fn(() => ({
      brand: 'devtools',
      model: 'iPhone 12',
      system: 'iOS 14.5',
      platform: 'ios',
      screenWidth: 390,
      screenHeight: 844,
      windowWidth: 390,
      windowHeight: 844,
    })),
    getStorageSync: vi.fn(() => ''),
    setStorageSync: vi.fn(),
    removeStorageSync: vi.fn(),
    clearStorageSync: vi.fn(),
    getStorageInfoSync: vi.fn(() => ({ keys: [], currentSize: 0, limitSize: 10000 })),
    request: vi.fn(),
    uploadFile: vi.fn(),
    downloadFile: vi.fn(),
    showToast: vi.fn(),
    hideToast: vi.fn(),
    showLoading: vi.fn(),
    hideLoading: vi.fn(),
    showModal: vi.fn(),
    showActionSheet: vi.fn(),
  }
}

/**
 * 创建 Pinia store mock
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
 * Mock 延迟
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 等待直到条件满足
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
 * 生成随机邮箱
 */
export function randomEmail(): string {
  return `test_${randomString(8)}@example.com`
}

/**
 * 生成随机手机号
 */
export function randomPhone(): string {
  return `1${randomNumber(3, 9)}${randomNumber(100000000, 999999999)}`
}

/**
 * Mock API 响应
 */
export function mockApiResponse<T>(data: T, delay = 100): Promise<T> {
  return new Promise(resolve => {
    setTimeout(() => resolve(data), delay)
  })
}

/**
 * Mock API 错误
 */
export function mockApiError(message: string, code = 500, delay = 100): Promise<never> {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject(new Error(message))
    }, delay)
  })
}

/**
 * 创建模拟的 Pinia 实例
 */
export function createPiniaInstance() {
  const { createPinia, setActivePinia } = require('pinia')
  const pinia = createPinia()
  setActivePinia(pinia)
  return pinia
}

/**
 * 清除所有 mocks
 */
export function clearAllMocks() {
  vi.clearAllMocks()
}

/**
 * 模拟 Vue 组件的 props
 */
export function mockProps<T extends Record<string, any>>(props: T): T {
  return {
    ...props,
  }
}

/**
 * 深度克隆对象
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/**
 * 格式化日期为测试友好的字符串
 */
export function formatDateForTest(date: Date): string {
  return date.toISOString().split('T')[0]
}

/**
 * 创建测试用的用户数据
 */
export function createTestUserData(overrides = {}) {
  return {
    id: randomString(20),
    nickname: `测试用户${randomNumber(1000, 9999)}`,
    avatar: 'https://example.com/avatar.jpg',
    is_active: true,
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * 创建测试用的帖子数据
 */
export function createTestPostData(overrides = {}) {
  return {
    id: randomString(20),
    content: `这是一条测试帖子 ${randomString(10)}`,
    images: [],
    mood: 'happy',
    is_anonymous: false,
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * 断言元素存在
 */
export function assertElementExists(wrapper: any, selector: string) {
  expect(wrapper.find(selector).exists()).toBe(true)
}

/**
 * 断言元素不存在
 */
export function assertElementNotExists(wrapper: any, selector: string) {
  expect(wrapper.find(selector).exists()).toBe(false)
}

/**
 * 断言文本内容
 */
export function assertTextContent(wrapper: any, selector: string, text: string) {
  expect(wrapper.find(selector).text()).toContain(text)
}
