/**
 * 小程序请求封装：baseURL + uni.request，便于后续加 token
 */
const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export type RequestOptions = Omit<UniApp.RequestOption, 'url'> & {
  url: string
  /** 是否不需要带 token（如登录接口） */
  noAuth?: boolean
}

function resolveUrl(url: string): string {
  if (url.startsWith('http')) return url
  const base = baseURL.replace(/\/$/, '')
  const path = url.startsWith('/') ? url : `/${url}`
  return `${base}${path}`
}

/** 从本地取 token（与登录逻辑一致即可） */
function getToken(): string {
  try {
    return uni.getStorageSync('token') || ''
  } catch {
    return ''
  }
}

export function request<T = unknown>(options: RequestOptions): Promise<T> {
  const url = resolveUrl(options.url)
  const token = options.noAuth ? '' : getToken()
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.header as Record<string, string>),
  }
  if (token) header.Authorization = `Bearer ${token}`

  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      url,
      header,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject(new Error((res.data as { detail?: string })?.detail || `HTTP ${res.statusCode}`))
        }
      },
      fail: (err) => reject(err),
    })
  })
}

export default request
