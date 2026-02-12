/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as userApi from '@/api/user'
import type { UserInfo, UserUpdateParams, UserProfileData } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  // 状态
  const currentUser = ref<UserInfo | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 请求去重：防止并发调用 fetchCurrentUser 导致多个请求
  let fetchCurrentUserPromise: Promise<boolean> | null = null

  // 计算属性
  const userId = computed(() => currentUser.value?.id || '')
  const anonymousName = computed(() => currentUser.value?.anonymous_name || '')
  const avatar = computed(() => currentUser.value?.avatar || '')
  const bio = computed(() => currentUser.value?.bio || '')
  const followerCount = computed(() => currentUser.value?.follower_count || 0)
  const followingCount = computed(() => currentUser.value?.following_count || 0)
  const postCount = computed(() => currentUser.value?.post_count || 0)
  const allowFollow = computed(() => currentUser.value?.allow_follow === 1)
  const allowComment = computed(() => currentUser.value?.allow_comment === 1)

  /**
   * 获取当前用户信息
   */
  async function fetchCurrentUser(): Promise<boolean> {
    // 如果正在请求中，返回现有的 promise（防止并发）
    if (fetchCurrentUserPromise) {
      return fetchCurrentUserPromise
    }

    // 创建新的请求 promise
    fetchCurrentUserPromise = (async () => {
      try {
        isLoading.value = true
        error.value = null
        const data = await userApi.getCurrentUser()
        currentUser.value = data
        return true
      } catch (e: unknown) {
        error.value = e instanceof Error ? e.message : '获取用户信息失败'
        return false
      } finally {
        isLoading.value = false
        fetchCurrentUserPromise = null  // 清除 promise 引用
      }
    })()

    return fetchCurrentUserPromise
  }

  /**
   * 更新当前用户信息
   */
  async function updateCurrentUser(params: UserUpdateParams): Promise<boolean> {
    try {
      isLoading.value = true
      error.value = null
      const data = await userApi.updateCurrentUser(params)
      currentUser.value = data
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '更新用户信息失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取指定用户的主页数据
   */
  async function fetchUserProfile(targetUserId: string): Promise<UserProfileData | null> {
    try {
      isLoading.value = true
      error.value = null
      const data = await userApi.getUserProfile(targetUserId)
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取用户主页失败'
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新本地用户信息（用于优化性能，减少请求）
   */
  function updateLocalUserInfo(partial: Partial<UserInfo>) {
    if (currentUser.value) {
      currentUser.value = { ...currentUser.value, ...partial }
    }
  }

  /**
   * 清空用户信息
   */
  function clearUserInfo() {
    currentUser.value = null
    error.value = null
  }

  /**
   * 登出时调用（清空用户信息和状态）
   */
  function logout() {
    clearUserInfo()
    error.value = null
  }

  return {
    // 状态
    currentUser,
    isLoading,
    error,

    // 计算属性
    userId,
    anonymousName,
    avatar,
    bio,
    followerCount,
    followingCount,
    postCount,
    allowFollow,
    allowComment,

    // 方法
    fetchCurrentUser,
    updateCurrentUser,
    fetchUserProfile,
    updateLocalUserInfo,
    clearUserInfo,
    logout,
  }
})
