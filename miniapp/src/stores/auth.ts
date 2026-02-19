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
   */
  async function login(code: string): Promise<boolean> {
    try {
      isLoading.value = true
      const response = await authApi.login(code)

      // 保存 token
      token.value = response.access_token
      await tokenStorage.saveToken(response.access_token, response.refresh_token, response.user.id)

      // 注意：不再在 authStore 中保存用户信息
      // 用户信息由调用方使用 userStore.fetchCurrentUser() 获取

      return true
    } catch (error) {
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 退出登录
   */
  function logout() {
    token.value = ''
    tokenStorage.clearToken()
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
