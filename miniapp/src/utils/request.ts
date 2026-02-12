/**
 * 小程序请求封装：baseURL + uni.request，便于后续加 token
 * 支持统一的错误处理和 loading 提示
 */
import { hideLoading, showLoading, showError } from './toast'
import { hmacSha256 } from './crypto'
import { getToken as getStoredToken, clearToken } from '@/api/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

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
}

function resolveUrl(url: string): string {
  if (url.startsWith('http')) return url
  const base = baseURL.replace(/\/$/, '')
  const path = url.startsWith('/') ? url : `/${url}`
  return `${base}${path}`
}

/**
 * 从本地取 token（带过期检查）
 */
/**
 * 检查 JWT token是否过期
 */
function isTokenExpired(token: string): boolean {
  if (!token) return true
  try {
    // JWT格式: header.payload.signature
    const parts = token.split('.')
    if (parts.length !== 3) return true

    // 解码payload (Base64) - 使用 uni-app 的 API
    const arrayBuffer = uni.base64ToArrayBuffer(parts[1])
    const decoded = new TextDecoder().decode(arrayBuffer)
    const payload = JSON.parse(decoded)

    if (!payload.exp) return true

    // exp是秒级时间戳，转换为毫秒比较
    const now = Math.floor(Date.now() / 1000)
    // 提前 5 分钟判定过期，避免临界点问题
    return now >= (payload.exp - 300)
  } catch {
    return true
  }
}

/**
 * 生成随机 nonce
 */
function generateNonce(): string {
  return Date.now().toString(36) + Math.random().toString(36).substring(2)
}

/**
 * 请求签名（使用 HMAC-SHA256）
 */
async function signRequest(url: string, method: string, data: any, timestamp: number, nonce: string): Promise<string> {
  // 按字母顺序排序参数
  const params: Record<string, any> = { url, method, timestamp, nonce, ...data }
  const sorted = Object.keys(params).sort()

  // 拼接字符串
  const str = sorted.map(k => `${k}=${params[k]}`).join('&')

  // 从环境变量获取 API 密钥（必须设置，否则抛出错误）
  const apiSecret = import.meta.env.VITE_API_SECRET
  if (!apiSecret) {
    console.error('VITE_API_SECRET 环境变量未设置')
    throw new Error('API Secret 未配置')
  }

  // 使用 HMAC-SHA256 签名
  return await hmacSha256(str, apiSecret)
}

/**
 * 从本地取 token（带过期检查）
 */
async function getToken(): Promise<string> {
  try {
    // 使用 auth.ts 中的 getToken（会自动解密）
    const token = await getStoredToken()

    // 检查是否过期
    if (token && isTokenExpired(token)) {
      // 清除过期的 token
      clearToken()
      return ''
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

    // 跳转到登录页（需要根据实际路由调整）
    uni.navigateTo({
      url: '/pages/login/index',
      fail: () => {
        // 如果 navigateTo 失败，尝试 switchTab
        uni.switchTab({
          url: '/pages/index/index',
          fail: () => {
            console.error('跳转登录页失败')
          },
        })
      },
    })

    return true // 已处理
  }

  // 显示错误提示
  showError(error.message)
  return false
}

let loadingCount = 0

/** 显示或隐藏 loading */
function manageLoading(show: boolean, text?: string) {
  if (show) {
    if (loadingCount === 0) {
      showLoading(text || '加载中...')
    }
    loadingCount++
  } else {
    loadingCount--
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
    ...rawOptions
  } = options

  const url = resolveUrl(rawOptions.url)
  const token = rawOptions.noAuth ? '' : await getToken()
  const timestamp = Date.now()
  const nonce = generateNonce()
  const signature = await signRequest(url, rawOptions.method || 'GET', rawOptions.data, timestamp, nonce)

  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(rawOptions.header as Record<string, string>),
  }
  if (token) header.Authorization = `Bearer ${token}`
  header['X-Timestamp'] = timestamp.toString()
  header['X-Nonce'] = nonce
  header['X-Signature'] = signature

  // 显示 loading
  if (shouldShowLoading) {
    manageLoading(true, loadingText)
  }

  return new Promise((resolve, reject) => {
    uni.request({
      ...rawOptions,
      url,
      header,
      success: (res) => {
        // 隐藏 loading
        if (shouldShowLoading) {
          manageLoading(false)
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
