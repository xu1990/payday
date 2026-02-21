/**
 * 认证状态管理
 *
 * 修复：移除重复的用户状态，统一使用 userStore
 * authStore 只负责认证相关的状态（token、登录状态）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import * as tokenStorage from '@/utils/tokenStorage'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>('')
  const isLoading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)

  /**
   * 初始化 - 从本地存储恢复 token
   */
  async function init() {
    const savedToken = await tokenStorage.getToken()
    if (savedToken) {
      token.value = savedToken
      // Token 存在，用户信息由 userStore 负责获取
    }
  }

  /**
   * 微信登录
   * @param code 微信登录授权码
   * @param phoneNumberCode 手机号授权码（可选）
   */
  async function login(code: string, phoneNumberCode?: string): Promise<boolean> {
    try {
      isLoading.value = true
      const response = await authApi.login(code, phoneNumberCode)

      // 保存 token
      token.value = response.access_token
      await tokenStorage.saveToken(response.access_token, response.refresh_token, response.user.id)

      // 多次验证 token 确实已存储成功（解决真机环境下存储异步问题）
      let storedToken = ''
      for (let i = 0; i < 5; i++) {
        await new Promise(resolve => setTimeout(resolve, 100)) // 延迟100ms
        storedToken = await tokenStorage.getToken()
        if (storedToken) {
          console.log(`[authStore] Token verified in storage (attempt ${i + 1}/5)`)
          break
        } else {
          console.warn(`[authStore] Token not found yet, retrying... (${i + 1}/5)`)
        }
      }

      if (!storedToken) {
        console.error('[authStore] Token verification failed: not found after multiple attempts')
        throw new Error('Token存储失败')
      }

      // 注意：不再在 authStore 中保存用户信息
      // 用户信息由调用方使用 userStore.fetchCurrentUser() 获取

      return true
    } catch (error) {
      console.error('[authStore] Login failed:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 退出登录
   */
  async function logout() {
    token.value = ''
    await tokenStorage.clearToken()
    // 注意：不再清除 userInfo，由 userStore 负责
  }

  return {
    // 状态
    token,
    isLoading,

    // 计算属性
    isLoggedIn,

    // 方法
    init,
    login,
    logout,
  }
})
