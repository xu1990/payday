import { defineStore } from 'pinia'

const TOKEN_KEY = 'payday_admin_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: (() => {
      try {
        return localStorage.getItem(TOKEN_KEY) || ''
      } catch {
        return ''
      }
    })(),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
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
