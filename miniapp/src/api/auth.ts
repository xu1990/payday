/**
 * 认证相关 API - 与 backend /api/v1/auth 一致
 */
import request from '@/utils/request'
import * as crypto from '@/utils/crypto'

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
 * 保存 Token 到本地存储（直接存储，使用 HTTPS 保护传输）
 *
 * SECURITY: 移除客户端加密的原因
 * 1. HTTPS 已提供传输安全保护
 * 2. 设备绑定密钥也存储在本地，加密无实际意义
 * 3. 微信小程序提供存储隔离，其他小程序无法直接读取
 * 4. 真正的安全由 JWT 签名 + 后端验证提供
 */
export async function saveToken(token: string, refreshToken?: string, userId?: string): Promise<void> {
  try {
    // SECURITY: Encrypt token before storage
    const encryptedToken = await crypto.encrypt(token)
    uni.setStorageSync(TOKEN_KEY, encryptedToken)
    if (refreshToken) {
      const encryptedRefreshToken = await crypto.encrypt(refreshToken)
      uni.setStorageSync(REFRESH_TOKEN_KEY, encryptedRefreshToken)
    }
    if (userId) uni.setStorageSync(USER_ID_KEY, userId)
  } catch (e) {
    // SECURITY: 存储失败可能表示存储空间不足或被禁用
    // 给用户明确的错误提示
    const errorMsg = e instanceof Error ? e.message : String(e)

    if (errorMsg.includes('quota') || errorMsg.includes('storage')) {
      uni.showModal({
        title: '存储失败',
        content: '浏览器存储空间不足，请清理缓存后重试',
        showCancel: false
      })
    } else if (errorMsg.includes('access') || errorMsg.includes('permission')) {
      uni.showModal({
        title: '存储失败',
        content: '存储权限被禁用，请在设置中允许后重试',
        showCancel: false
      })
    } else {
      uni.showModal({
        title: '存储失败',
        content: '无法保存登录信息，请检查浏览器设置',
        showCancel: false
      })
    }

    console.error('Token save failed:', e)
    throw e // 重新抛出，让调用方处理
  }
}

/**
 * 获取本地存储的 Token（直接读取）
 */
export async function getToken(): Promise<string> {
  try {
    const encryptedToken = uni.getStorageSync(TOKEN_KEY)
    if (!encryptedToken) {
      console.warn('[auth] No token found in storage')
      return ''
    }
    // SECURITY: Decrypt token
    const decryptedToken = await crypto.decrypt(encryptedToken)
    return decryptedToken || ''
  } catch (error) {
    console.error('[auth] Token retrieval failed:', error)
    return ''
  }
}

/**
 * 获取本地存储的 Refresh Token（直接读取）
 */
export async function getRefreshToken(): Promise<string> {
  try {
    const token = uni.getStorageSync(REFRESH_TOKEN_KEY)
    if (!token) {
      console.warn('[auth] No refresh token found in storage')
      return ''
    }
    return token
  } catch (error) {
    console.error('[auth] Refresh token retrieval failed:', error)
    return ''
  }
}

/**
 * 获取本地存储的 User ID（直接读取）
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
    console.error('Token clear failed:', e)
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
