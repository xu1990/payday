/**
 * 通知状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as notificationApi from '@/api/notification'

export type NotificationType = 'comment' | 'reply' | 'like' | 'follow' | 'system'
export type NotificationStatus = 'read' | 'unread'

export interface Notification {
  id: string
  user_id: string
  type: NotificationType
  title: string
  content: string
  related_id: string | null
  related_type: string | null
  status: NotificationStatus
  created_at: string
  // 额外字段（来自关联数据）
  actor?: {
    id: string
    anonymous_name: string
    avatar: string | null
  }
}

export const useNotificationStore = defineStore('notification', () => {
  // 状态
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const isLoading = ref(false)
  const isLoadingMore = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)

  // 分页状态
  const offset = ref(0)
  const pageSize = 20

  // 计算属性
  const hasNotifications = computed(() => notifications.value.length > 0)
  const hasUnread = computed(() => unreadCount.value > 0)

  /**
   * 获取通知列表
   */
  async function fetchNotifications(refresh = false): Promise<boolean> {
    if (refresh) {
      offset.value = 0
      notifications.value = []
    }

    if (isLoading.value || !hasMore.value) return false

    try {
      isLoading.value = !refresh
      isLoadingMore.value = refresh

      const data = await notificationApi.getNotifications({
        limit: pageSize,
        offset: offset.value,
      })

      if (refresh) {
        notifications.value = data.items
      } else {
        notifications.value.push(...data.items)
      }

      offset.value += data.items.length
      hasMore.value = data.items.length === pageSize
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取通知失败'
      return false
    } finally {
      isLoading.value = false
      isLoadingMore.value = false
    }
  }

  /**
   * 获取未读数量
   */
  async function fetchUnreadCount(): Promise<boolean> {
    try {
      const data = await notificationApi.getUnreadCount()
      unreadCount.value = data.count
      return true
    } catch (e: unknown) {
      return false
    }
  }

  /**
   * 标记单条通知为已读
   */
  async function markAsRead(notificationId: string): Promise<boolean> {
    try {
      await notificationApi.markAsRead(notificationId)

      // 更新本地状态
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification && notification.status === 'unread') {
        notification.status = 'read'
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      return true
    } catch (e: unknown) {
      return false
    }
  }

  /**
   * 标记所有通知为已读
   */
  async function markAllAsRead(): Promise<boolean> {
    try {
      await notificationApi.markAllAsRead()

      // 更新本地状态
      notifications.value.forEach(n => {
        if (n.status === 'unread') {
          n.status = 'read'
        }
      })
      unreadCount.value = 0
      return true
    } catch (e: unknown) {
      return false
    }
  }

  /**
   * 删除通知
   */
  async function deleteNotification(notificationId: string): Promise<boolean> {
    try {
      await notificationApi.deleteNotification(notificationId)

      // 更新本地状态
      const index = notifications.value.findIndex(n => n.id === notificationId)
      if (index !== -1) {
        const notification = notifications.value[index]
        if (notification.status === 'unread') {
          unreadCount.value = Math.max(0, unreadCount.value - 1)
        }
        notifications.value.splice(index, 1)
      }
      return true
    } catch (e: unknown) {
      return false
    }
  }

  /**
   * 清空所有通知
   */
  async function clearAll(): Promise<boolean> {
    try {
      await notificationApi.clearAll()
      notifications.value = []
      unreadCount.value = 0
      return true
    } catch (e: unknown) {
      return false
    }
  }

  /**
   * 添加新通知（用于实时推送）
   */
  function addNotification(notification: Notification) {
    notifications.value.unshift(notification)
    if (notification.status === 'unread') {
      unreadCount.value++
    }
  }

  /**
   * 重置状态
   */
  function reset() {
    notifications.value = []
    unreadCount.value = 0
    offset.value = 0
    hasMore.value = true
    error.value = null
  }

  return {
    // 状态
    notifications,
    unreadCount,
    isLoading,
    isLoadingMore,
    error,
    hasMore,

    // 计算属性
    hasNotifications,
    hasUnread,

    // 方法
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
    addNotification,
    reset,
  }
})
