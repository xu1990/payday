/**
 * 通知服务 - 处理通知相关业务逻辑
 */
import { BaseService } from './base/BaseService'

export interface NotificationItem {
  id: string
  type: string
  title: string
  content: string
  is_read: boolean
  created_at: string
}

export class NotificationService extends BaseService {
  protected get baseUrl() {
    return '/api/v1/notifications'
  }

  /**
   * 获取通知列表
   */
  async getNotifications(params: { limit?: number; offset?: number }) {
    return this.get<NotificationItem[]>('', params)
  }

  /**
   * 获取未读数量
   */
  async getUnreadCount() {
    return this.get<{ count: number }>('/unread-count')
  }

  /**
   * 标记为已读
   */
  async markAsRead(notificationId: string) {
    return this.post<boolean>(`/${notificationId}/read`)
  }

  /**
   * 标记全部已读
   */
  async markAllAsRead() {
    return this.post<boolean>('/read-all')
  }
}

// 导出单例
export const notificationService = new NotificationService()
