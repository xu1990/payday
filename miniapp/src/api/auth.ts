/**
 * 认证相关 API - 与 backend /api/v1/auth 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/auth'

export interface LoginRequest {
  code: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    anonymous_name: string
    avatar: string | null
  }
}

/**
 * 微信小程序登录
 * @param code 微信 wx.login() 返回的 code
 */
export function login(code: string): Promise<LoginResponse> {
  return request<LoginResponse>({
    url: `${PREFIX}/login`,
    method: 'POST',
    data: { code },
    noAuth: true,
  })
}

/**
 * 保存 Token 到本地存储
 *
 * SECURITY NOTE: Token 明文存储，依赖 JWT 签名保护安全
 * 客户端加密无实际安全意义（密钥暴露在打包后的代码中）
 * 真正的安全来自：
 * 1. JWT 短期有效期（15分钟）+ Refresh Token 轮换
 * 2. 后端验证和签名检查
 * 3. HTTPS 传输加密
 */
export async function saveToken(token: string): Promise<void> {
  try {
    uni.setStorageSync('token', token)
  } catch (e) {
    console.error('保存 token 失败:', e)
  }
}

/**
 * 获取本地存储的 Token
 */
export async function getToken(): Promise<string> {
  try {
    return uni.getStorageSync('token') || ''
  } catch {
    return ''
  }
}

/**
 * 清除本地存储的 Token
 */
export function clearToken(): void {
  try {
    uni.removeStorageSync('token')
  } catch (e) {
    console.error('清除 token 失败:', e)
  }
}

/**
 * 检查是否已登录
 */
export async function isLoggedIn(): Promise<boolean> {
  const token = await getToken()
  return !!token
}

export default {
  login,
  saveToken,
  getToken,
  clearToken,
  isLoggedIn,
}
