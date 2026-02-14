/*
 * Vitest 测试环境设置文件 - Miniapp
 * Mock uni-app 全局对象和环境
 */
import { vi } from 'vitest'

// Mock uni-app 全局对象
global.uni = {
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

// Mock Pinia stores
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: null,
    accessToken: '',
    refreshToken: '',
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshTokens: vi.fn(),
  }),
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    userInfo: null,
    updateUser: vi.fn(),
    clearUser: vi.fn(),
  }),
}))

vi.mock('@/stores/post', () => ({
  usePostStore: () => ({
    posts: [],
    hotPosts: [],
    latestPosts: [],
    fetchPosts: vi.fn(),
    fetchHotPosts: vi.fn(),
    fetchLatestPosts: vi.fn(),
  }),
}))
