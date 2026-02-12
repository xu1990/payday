import { defineStore } from 'pinia'

const TOKEN_KEY = 'payday_admin_token'

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
 * 4. In production: Use HttpOnly cookies instead of localStorage
 */

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
      try {
        const token = localStorage.getItem(TOKEN_KEY) || ''
        if (!token) return ''

        // 检查token是否过期
        if (token && isTokenExpired(token)) {
          // 过期则清除
          localStorage.removeItem(TOKEN_KEY)
          return ''
        }

        return token
      } catch {
        return ''
      }
    })(),
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
    setToken(t: string) {
      this.token = t
      try {
        if (t) {
          localStorage.setItem(TOKEN_KEY, t)
        } else {
          localStorage.removeItem(TOKEN_KEY)
        }
      } catch (error) {
        console.error('Failed to save token to localStorage:', error)
      }
    },
    logout() {
      this.token = ''
      try {
        localStorage.removeItem(TOKEN_KEY)
      } catch (error) {
        console.error('Failed to remove token from localStorage:', error)
      }
    },
  },
})
