/**
 * 认证服务 - 处理认证相关业务逻辑
 */
import { BaseService } from './base/BaseService'

export class AuthService extends BaseService {
  protected get baseUrl() {
    return '/api/v1/auth'
  }

  /**
   * 微信登录
   */
  async loginWithCode(code: string) {
    return this.post<{ token: string; user: { id: string } }>('/login', { code })
  }

  /**
   * 刷新 Token
   */
  async refreshToken() {
    return this.post<{ token: string }>('/refresh')
  }

  /**
   * 登出
   */
  async logout() {
    return this.post<boolean>('/logout')
  }
}

// 导出单例
export const authService = new AuthService()
