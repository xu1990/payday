import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'payday_admin_token'
const CSRF_KEY = 'payday_admin_csrf'

/**
 * SECURITY NOTE: Client-side token encryption is removed
 *
 * Why: Vite environment variables with VITE_ prefix are exposed in client bundle
 * Client-side encryption provides NO real security - anyone can inspect the built JavaScript
 *
 * Real security comes from:
 * 1. JWT cryptographic signatures (already implemented on backend)
 * 2. Short token expiration (15 min) with refresh token rotation
 * 3. Backend validation and revocation
 * 4. CSRF tokens for state-changing operations (newly implemented)
 */

/**
 * 检测 localStorage 是否可用
 */
function isStorageAvailable(): boolean {
  try {
    const test = '__storage_test__'
    localStorage.setItem(test, test)
    localStorage.removeItem(test)
    return true
  } catch {
    return false
  }
}

/**
 * 安全的 localStorage 操作，失败时显示错误提示
 */
function safeSetItem(key: string, value: string): boolean {
  try {
    localStorage.setItem(key, value)
    return true
  } catch (error) {
    // 检测具体错误原因
    const errorMessage = error instanceof Error ? error.message : String(error)

    if (errorMessage.includes('quota')) {
      ElMessage.error('浏览器存储空间不足，请清理缓存后重试')
    } else if (errorMessage.includes('access')) {
      ElMessage.error('浏览器存储功能被禁用，请在设置中允许后重试')
    } else {
      ElMessage.error('无法保存登录信息，请检查浏览器设置')
    }
    return false
  }
}

/**
 * 安全的 localStorage 删除操作，失败时显示警告
 */
function safeRemoveItem(key: string): boolean {
  try {
    localStorage.removeItem(key)
    return true
  } catch (error) {
    console.warn('Failed to remove from localStorage:', error)
    return false
  }
}

/**
 * 安全的 localStorage 读取操作，失败时返回空字符串
 */
function safeGetItem(key: string): string {
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

/**
 * 检查JWT token是否过期
 */
function isTokenExpired(token: string): boolean {
  if (!token) return true

  try {
    // JWT格式: header.payload.signature
    const parts = token.split('.')
    if (parts.length !== 3) return true

    // 解码payload (Base64)
    const payload = JSON.parse(atob(parts[1]))

    // 检查exp声明
    if (!payload.exp) return true

    // exp是秒级时间戳，转换为毫秒比较
    const now = Math.floor(Date.now() / 1000)
    return now >= payload.exp
  } catch {
    // 解码失败则视为过期
    return true
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: (() => {
      // 使用安全读取函数
      const token = safeGetItem(TOKEN_KEY)
      if (!token) return ''

      // 检查token是否过期
      if (token && isTokenExpired(token)) {
        // 过期则清除
        safeRemoveItem(TOKEN_KEY)
        return ''
      }

      return token
    })(),
    refreshToken: safeGetItem('payday_admin_refresh_token'),
    csrfToken: safeGetItem(CSRF_KEY),
    // 标记存储是否可用
    storageAvailable: isStorageAvailable(),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token && !isTokenExpired(state.token),
    /** 验证当前 token 是否具有 admin scope */
    hasAdminScope: (state) => {
      if (!state.token || isTokenExpired(state.token)) return false
      try {
        // JWT格式: header.payload.signature
        const parts = state.token.split('.')
        if (parts.length !== 3) return false
        const payload = JSON.parse(atob(parts[1]))
        return payload.scope === 'admin'
      } catch {
        return false
      }
    },
  },
  actions: {
    setToken(t: string, csrfToken?: string, refreshToken?: string) {
      this.token = t

      // 处理csrf token
      if (csrfToken !== undefined) {
        this.csrfToken = csrfToken
      }

      // 处理refresh token：如果传入了新值则更新，否则保留旧值
      if (refreshToken !== undefined) {
        this.refreshToken = refreshToken
        if (refreshToken) {
          safeSetItem('payday_admin_refresh_token', refreshToken)
        } else {
          safeRemoveItem('payday_admin_refresh_token')
        }
      }

      // 如果存储不可用，给出警告
      if (!this.storageAvailable) {
        ElMessage.warning('浏览器存储不可用，每次刷新都需要重新登录')
        return
      }

      // 使用安全存储函数
      if (t) {
        safeSetItem(TOKEN_KEY, t)
      } else {
        safeRemoveItem(TOKEN_KEY)
      }
      if (csrfToken !== undefined) {
        if (csrfToken) {
          safeSetItem(CSRF_KEY, csrfToken)
        } else {
          safeRemoveItem(CSRF_KEY)
        }
      }
    },
    logout() {
      this.token = ''
      this.refreshToken = ''
      this.csrfToken = ''
      safeRemoveItem(TOKEN_KEY)
      safeRemoveItem('payday_admin_refresh_token')
      safeRemoveItem(CSRF_KEY)
    },
  },
})
