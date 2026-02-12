import { defineStore } from 'pinia'
import CryptoJS from 'crypto-js'

const TOKEN_KEY = 'payday_admin_token'
// 必须从环境变量获取加密密钥，生产环境不允许使用默认值
const ENCRYPTION_KEY = import.meta.env.VITE_TOKEN_ENCRYPTION_KEY

if (!ENCRYPTION_KEY) {
  throw new Error('VITE_TOKEN_ENCRYPTION_KEY environment variable must be set in production')
}

/**
 * 加密 token
 */
function encryptToken(token: string): string {
  return CryptoJS.AES.encrypt(token, ENCRYPTION_KEY).toString()
}

/**
 * 解密 token
 */
function decryptToken(encrypted: string): string {
  try {
    const bytes = CryptoJS.AES.decrypt(encrypted, ENCRYPTION_KEY)
    return bytes.toString(CryptoJS.enc.Utf8)
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
      try {
        const encrypted = localStorage.getItem(TOKEN_KEY) || ''
        if (!encrypted) return ''

        // 解密 token
        const token = decryptToken(encrypted)

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
          const encrypted = encryptToken(t)
          localStorage.setItem(TOKEN_KEY, encrypted)
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
