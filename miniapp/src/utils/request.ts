/**
 * 小程序请求封装：baseURL + uni.request，便于后续加 token
 * 支持统一的错误处理和 loading 提示
 *
 * SECURITY: 移除客户端请求签名功能
 * - 客户端签名不安全，因为密钥会暴露在客户端代码中
 * - 改用 HTTPS + JWT 认证，由后端验证 token 有效性
 * - 后端通过其他机制（如速率限制）防止滥用
 */
import { hideLoading, showLoading, showError } from './toast'
import { getToken as getStoredToken, getRefreshToken, getUserId, saveToken, clearToken, refreshAccessToken } from '@/api/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

// 防止多个请求同时尝试刷新 token
let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null
let refreshAttempts = 0
const MAX_REFRESH_ATTEMPTS = 3

export type RequestOptions = Omit<UniApp.RequestOption, 'url'> & {
  url: string
  /** 是否不需要带 token（如登录接口） */
  noAuth?: boolean
  /** 是否显示 loading 提示 */
  showLoading?: boolean
  /** loading 提示文字 */
  loadingText?: string
  /** 是否自动显示错误提示 */
  showError?: boolean
  /** 自定义错误处理 */
  errorHandler?: (error: Error) => void | boolean
  /** 如果设置了此选项，具有相同abortKey的请求会被取消 */
  abortKey?: string
}

function resolveUrl(url: string): string {
  if (url.startsWith('http')) return url
  const base = baseURL.replace(/\/$/, '')
  const path = url.startsWith('/') ? url : `/${url}`
  return `${base}${path}`
}

/**
 * 检查 JWT token是否过期
 */
function isTokenExpired(token: string): boolean {
  if (!token) return true
  try {
    // JWT格式: header.payload.signature
    const parts = token.split('.')
    if (parts.length !== 3) return true

    // 解码payload (Base64) - 使用跨平台兼容的方法
    let decoded: string
    // #ifdef H5
    // H5环境使用 atob 或 polyfill
    if (typeof atob !== 'undefined') {
      decoded = atob(parts[1])
    } else {
      // 简单的 Base64 解码（仅适用于URL-safe Base64）
      decoded = decodeURIComponent(escape(atob(parts[1])))
    }
    // #endif

    // #ifndef H5
    // 小程序环境使用 uni-app API
    const arrayBuffer = uni.base64ToArrayBuffer(parts[1])
    decoded = new TextDecoder().decode(arrayBuffer)
    // #endif

    const payload = JSON.parse(decoded)

    if (!payload.exp) return true

    // exp是秒级时间戳，转换为毫秒比较
    const now = Math.floor(Date.now() / 1000)
    // 提前 30 秒判定过期，避免临界点问题
    return now >= (payload.exp - 30)
  } catch {
    return true
  }
}

/**
 * 尝试刷新 access token
 * SECURITY: 改进队列机制和重试限制，防止竞态条件
 */
async function tryRefreshToken(): Promise<boolean> {
  // 如果正在刷新，等待现有刷新完成
  if (refreshPromise) {
    try {
      return await refreshPromise
    } catch {
      // 先前刷新失败，尝试再次刷新
    }
  }

  // 检查重试次数
  if (refreshAttempts >= MAX_REFRESH_ATTEMPTS) {
    console.error('[request] Max refresh attempts reached, clearing tokens')
    clearToken()
    refreshAttempts = 0
    return false
  }

  refreshAttempts++
  isRefreshing = true

  refreshPromise = (async () => {
    try {
      const refreshToken = await getRefreshToken()
      const userId = getUserId()

      if (!refreshToken || !userId) {
        return false
      }

      const result = await refreshAccessToken(refreshToken, userId)

      // 保存新的 tokens
      await saveToken(result.access_token, result.refresh_token, userId)

      // 重置重试计数
      refreshAttempts = 0
      return true
    } catch (error) {
      console.error('[request] Token refresh failed:', error)

      // 如果达到最大重试次数，清除所有 token
      if (refreshAttempts >= MAX_REFRESH_ATTEMPTS) {
        clearToken()
        refreshAttempts = 0
      }

      return false
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()

  return refreshPromise
}

/**
 * 从本地取 token（带过期检查和自动刷新）
 */
async function getToken(): Promise<string> {
  try {
    // 使用 auth.ts 中的 getToken（会自动解密）
    let token = await getStoredToken()

    // 检查是否过期
    if (token && isTokenExpired(token)) {
      // 尝试刷新 token
      const refreshed = await tryRefreshToken()
      if (refreshed) {
        // 刷新成功，获取新 token
        token = await getStoredToken()
      } else {
        // 刷新失败，清除 token
        token = ''
      }
    }

    return token
  } catch {
    return ''
  }
}

/** 处理 HTTP 错误状态码 */
function handleHttpError(statusCode: number, data?: unknown): Error {
  const detail = (data as { detail?: string })?.detail

  const statusMessages: Record<number, string> = {
    400: detail || '请求参数错误',
    401: '登录已过期，请重新登录',
    403: '没有权限访问',
    404: '请求的资源不存在',
    429: '操作太频繁，请稍后再试',
    500: '服务器错误，请稍后重试',
    502: '网关错误，请稍后重试',
    503: '服务暂时不可用',
  }

  const message = statusMessages[statusCode] || `请求失败 (${statusCode})`
  return new Error(message)
}

/** 默认错误处理 */
function defaultErrorHandler(error: Error): boolean {
  // 401 错误特殊处理 - 跳转到登录页
  if (error.message.includes('登录已过期')) {
    // 清除 token
    clearToken()

    // 使用 reLaunch 清除页面栈并跳转到登录页
    uni.reLaunch({
      url: '/pages/login/index',
    })

    return true // 已处理
  }

  // 显示错误提示
  showError(error.message)
  return false
}

let loadingCount = 0
// 用于跟踪当前最新的请求ID
let currentRequestId = 0
// 存储活动的请求ID，用于取消
const activeRequests = new Map<string, number>()

/**
 * 生成下一个请求ID
 */
function getNextRequestId(): number {
  return ++currentRequestId
}

/** 显示或隐藏 loading */
function manageLoading(show: boolean, text?: string) {
  if (show) {
    if (loadingCount === 0) {
      showLoading(text || '加载中...')
    }
    loadingCount++
  } else {
    // 确保 loadingCount 不会变成负数
    loadingCount = Math.max(0, loadingCount - 1)
    if (loadingCount <= 0) {
      loadingCount = 0
      hideLoading()
    }
  }
}

export async function request<T = unknown>(options: RequestOptions): Promise<T> {
  const {
    showLoading: shouldShowLoading = false,
    loadingText,
    showError: shouldShowError = true,
    errorHandler: customErrorHandler,
    abortKey,
    ...rawOptions
  } = options

  // 生成此请求的唯一ID
  const requestId = getNextRequestId()

  // 如果有abortKey，记录此请求ID
  if (abortKey) {
    activeRequests.set(abortKey, requestId)
  }

  const url = resolveUrl(rawOptions.url)
  const token = rawOptions.noAuth ? '' : await getToken()

  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(rawOptions.header as Record<string, string>),
  }
  if (token) header.Authorization = `Bearer ${token}`

  // 显示 loading
  if (shouldShowLoading) {
    manageLoading(true, loadingText)
  }

  return new Promise((resolve, reject) => {
    uni.request({
      ...rawOptions,
      url,
      header,
      timeout: 30000,  // 30秒超时，防止请求长时间挂起
      success: (res) => {
        // 隐藏 loading
        if (shouldShowLoading) {
          manageLoading(false)
        }

        // 检查此请求是否已被新的请求取代
        if (abortKey && activeRequests.get(abortKey) !== requestId) {
          // 此请求已被取消，忽略响应
          return
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          const error = handleHttpError(res.statusCode, res.data)

          // 错误处理
          if (customErrorHandler) {
            const handled = customErrorHandler(error)
            if (!handled && shouldShowError) {
              defaultErrorHandler(error)
            }
          } else if (shouldShowError) {
            defaultErrorHandler(error)
          }

          reject(error)
        }
      },
      fail: (err) => {
        // 隐藏 loading
        if (shouldShowLoading) {
          manageLoading(false)
        }

        // 检查此请求是否已被新的请求取代
        if (abortKey && activeRequests.get(abortKey) !== requestId) {
          // 此请求已被取消，忽略错误
          return
        }

        const error = new Error(err.errMsg || '网络请求失败')

        // 错误处理
        if (customErrorHandler) {
          const handled = customErrorHandler(error)
          if (!handled && shouldShowError) {
            defaultErrorHandler(error)
          }
        } else if (shouldShowError) {
          defaultErrorHandler(error)
        }

        reject(error)
      },
    })
  })
}

export default request
