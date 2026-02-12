import { defineStore } from 'pinia'

const TOKEN_KEY = 'payday_admin_token'

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
  },
  actions: {
    setToken(t: string) {
      this.token = t
      try {
        if (t) localStorage.setItem(TOKEN_KEY, t)
        else localStorage.removeItem(TOKEN_KEY)
      } catch {}
    },
    logout() {
      this.token = ''
      try {
        localStorage.removeItem(TOKEN_KEY)
      } catch {}
    },
  },
})
