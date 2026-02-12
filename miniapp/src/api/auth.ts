/**
 * 认证相关 API - 与 backend /api/v1/auth 一致
 */
import request from '@/utils/request'
import { encrypt, decrypt } from '@/utils/crypto'

const PREFIX = '/api/v1/auth'
const TOKEN_KEY = 'payday_token'
const REFRESH_TOKEN_KEY = 'payday_refresh_token'
const USER_ID_KEY = 'payday_user_id'

export interface LoginRequest {
  code: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: string
    anonymous_name: string
    avatar: string | null
  }
}

export interface RefreshTokenRequest {
  refresh_token: string
  user_id: string
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
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
 * 刷新 Access Token
 * @param refreshToken 刷新令牌
 * @param userId 用户ID
 */
export function refreshAccessToken(refreshToken: string, userId: string): Promise<RefreshTokenResponse> {
  return request<RefreshTokenResponse>({
    url: `${PREFIX}/refresh`,
    method: 'POST',
    data: { refresh_token: refreshToken, user_id: userId },
    noAuth: true,
  })
}

/**
 * 保存 Token 到本地存储（使用 AES-GCM 加密）
 *
 * SECURITY: 使用设备绑定的密钥加密存储 Token
 * 虽然密钥存储在本地，但加密可以防止：
 * 1. 其他小程序通过 uni.getStorageSync() 直接读取
 * 2. 设备备份/取证时直接获取明文 token
 * 3. 调试时意外泄露 token
 */
export async function saveToken(token: string, refreshToken?: string, userId?: string): Promise<void> {
  try {
    const encrypted = await encrypt(token)
    uni.setStorageSync(TOKEN_KEY, encrypted)

    // 同时保存 refresh token 和 user_id
    if (refreshToken) {
      const encryptedRefresh = await encrypt(refreshToken)
      uni.setStorageSync(REFRESH_TOKEN_KEY, encryptedRefresh)
    }
    if (userId) {
      uni.setStorageSync(USER_ID_KEY, userId)
    }
  } catch (e) {
    // Token save failed
    console.error('Token save failed:', e)
  }
}

/**
 * 获取本地存储的 Token（解密）
 */
export async function getToken(): Promise<string> {
  try {
    const encrypted = uni.getStorageSync(TOKEN_KEY)
    if (!encrypted) return ''

    const decrypted = await decrypt(encrypted)
    if (!decrypted) {
      console.warn('[auth] Token decryption returned empty')
      return ''
    }
    return decrypted
  } catch (error) {
    console.error('[auth] Token retrieval failed:', error)
    // 清理可能损坏的token
    try {
      uni.removeStorageSync(TOKEN_KEY)
    } catch (e) {
      // 忽略清理错误
    }
    return ''
  }
}

/**
 * 获取本地存储的 Refresh Token（解密）
 */
export async function getRefreshToken(): Promise<string> {
  try {
    const encrypted = uni.getStorageSync(REFRESH_TOKEN_KEY)
    if (!encrypted) return ''

    const decrypted = await decrypt(encrypted)
    if (!decrypted) {
      console.warn('[auth] Refresh token decryption returned empty')
      return ''
    }
    return decrypted
  } catch (error) {
    console.error('[auth] Refresh token retrieval failed:', error)
    return ''
  }
}

/**
 * 获取本地存储的 User ID
 */
export function getUserId(): string {
  try {
    return uni.getStorageSync(USER_ID_KEY) || ''
  } catch (error) {
    console.error('[auth] User ID retrieval failed:', error)
    return ''
  }
}

/**
 * 清除本地存储的 Token
 */
export function clearToken(): void {
  try {
    uni.removeStorageSync(TOKEN_KEY)
    uni.removeStorageSync(REFRESH_TOKEN_KEY)
    uni.removeStorageSync(USER_ID_KEY)
  } catch (e) {
    // Token clear failed
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
  getRefreshToken,
  getUserId,
  clearToken,
  isLoggedIn,
  refreshAccessToken,
}
