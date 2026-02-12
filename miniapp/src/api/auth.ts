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
 * 保存 Token 到本地存储（加密版本）
 */
import { encrypt, decrypt } from '@/utils/crypto'

export async function saveToken(token: string): Promise<void> {
  try {
    const encrypted = await encrypt(token)
    uni.setStorageSync('token', encrypted)
  } catch (e) {
    console.error('保存 token 失败:', e)
  }
}

/**
 * 获取本地存储的 Token（解密版本）
 */
export async function getToken(): Promise<string> {
  try {
    const encrypted = uni.getStorageSync('token') || ''
    if (!encrypted) return ''
    return await decrypt(encrypted)
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
