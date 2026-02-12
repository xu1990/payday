/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import type * as AuthType from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>('')
  const userInfo = ref<AuthType.LoginResponse['user'] | null>(null)
  const isLoading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userId = computed(() => userInfo.value?.id || '')
  const anonymousName = computed(() => userInfo.value?.anonymous_name || '')
  const avatar = computed(() => userInfo.value?.avatar || '')

  /**
   * 初始化 - 从本地存储恢复 token
   */
  function init() {
    const savedToken = authApi.getToken()
    if (savedToken) {
      token.value = savedToken
      // Token 存在但用户信息可能需要重新获取
      // 这里暂时只恢复 token，用户信息由调用方决定是否重新获取
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
      authApi.saveToken(response.access_token)

      // 保存用户信息
      userInfo.value = response.user

      return true
    } catch (error) {
      console.error('登录失败:', error)
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
    userInfo.value = null
    authApi.clearToken()
  }

  /**
   * 设置用户信息
   */
  function setUserInfo(info: AuthType.LoginResponse['user']) {
    userInfo.value = info
  }

  return {
    // 状态
    token,
    userInfo,
    isLoading,

    // 计算属性
    isLoggedIn,
    userId,
    anonymousName,
    avatar,

    // 方法
    init,
    login,
    logout,
    setUserInfo,
  }
})
