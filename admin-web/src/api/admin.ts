import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

/**
 * CSRF 保护说明：
 *
 * 当前实现：后端设置httpOnly cookie，前端通过localStorage存储CSRF token
 * 请求时在X-CSRF-Token header中发送CSRF token
 *
 * 改进方案：添加token刷新队列机制，防止并发刷新请求冲突
 */

/**
 * 检测是否有请求正在刷新token
 */
let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null
// 存储等待重试的请求
let failedQueue: Array<(token: string) => void> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => prom(error || token))
  failedQueue = []
}

const adminApi = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

// 请求拦截器：添加token
adminApi.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    config.headers.Authorization = `Bearer ${authStore.token}`
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理401错误
adminApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config

    // 如果不是401错误或已经重试过，直接拒绝
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    // 如果正在刷新，将请求加入队列
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          resolve(adminApi(originalRequest))
        })
      }).catch(err => {
        return Promise.reject(err)
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    // 开始刷新token
    refreshPromise = (async () => {
      try {
        const refreshToken = authStore.refreshToken
        const userId = authStore.userId

        const { data } = await adminApi.post('/api/v1/admin/auth/refresh', {
          refresh_token: refreshToken,
          user_id: userId
        })

        // 更新token
        authStore.setToken(data.access_token, data.csrf_token, data.refresh_token)

        // 处理队列中的请求
        processQueue(null, data.access_token)

        isRefreshing = false
        return true
      } catch (refreshError) {
        console.error('[adminApi] Token refresh failed:', refreshError)

        // 刷新失败，清除token并处理队列
        processQueue(refreshError, null)
        authStore.logout()

        isRefreshing = false
        return false
      }
    })()

    try {
      const refreshed = await refreshPromise
      if (refreshed) {
        // 重试原始请求
        const newToken = authStore.token
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return adminApi(originalRequest)
      }
    } catch (retryError) {
      return Promise.reject(retryError)
    }

    return Promise.reject(error)
  }
)

export default adminApi