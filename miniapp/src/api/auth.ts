/**
 * 认证相关 API - 与 backend /api/v1/auth 一致
 *
 * 只负责 API 调用，token 存储由 utils/tokenStorage 管理
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/auth'

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

export default {
  login,
  refreshAccessToken,
}
