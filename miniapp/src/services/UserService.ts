/**
 * 用户服务 - 处理用户相关业务逻辑
 */
import { BaseService } from './base/BaseService'
import type { UserInfo } from '@/api/user'

export class UserService extends BaseService {
  protected get baseUrl() {
    return '/api/v1/users'
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser() {
    return this.get<UserInfo>('/me')
  }

  /**
   * 获取用户详情
   */
  async getUserProfile(userId: string) {
    return this.get<UserInfo>(`/${userId}`)
  }

  /**
   * 更新用户信息
   */
  async updateProfile(data: { anonymous_name?: string; avatar_url?: string; bio?: string }) {
    return this.put<UserInfo>('/me', data)
  }

  /**
   * 关注用户
   */
  async followUser(userId: string) {
    return this.post<boolean>(`/${userId}/follow`)
  }

  /**
   * 取消关注
   */
  async unfollowUser(userId: string) {
    return this.delete<boolean>(`/${userId}/follow`)
  }

  /**
   * 获取粉丝列表
   */
  async getFollowers(userId: string, params?: { limit?: number; offset?: number }) {
    return this.get<UserInfo[]>(`/${userId}/followers`, params)
  }

  /**
   * 获取关注列表
   */
  async getFollowing(userId: string, params?: { limit?: number; offset?: number }) {
    return this.get<UserInfo[]>(`/${userId}/following`, params)
  }
}

// 导出单例
export const userService = new UserService()
