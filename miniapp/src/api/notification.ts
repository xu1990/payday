/**
 * 通知 - 与 backend /api/v1/notifications 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/notifications'

export interface NotificationItem {
  id: string
  user_id: string
  type: string
  title: string
  content: string | null
  related_id: string | null
  is_read: boolean
  created_at: string
}

export interface NotificationListResult {
  items: NotificationItem[]
  total: number
  unread_count: number
}

/** 通知列表（分页），含 total、unread_count */
export function getNotificationList(params?: {
  unread_only?: boolean
  limit?: number
  offset?: number
}) {
  const { unread_only, limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  if (unread_only !== undefined) q.set('unread_only', String(unread_only))
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<NotificationListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 未读数量 */
export function getUnreadCount() {
  return request<{ unread_count: number }>({
    url: `${PREFIX}/unread_count`,
    method: 'GET',
  })
}

/** 标记已读：传 notification_ids 为部分，传 all: true 为全部 */
export function markRead(body: { notification_ids?: string[]; all?: boolean }) {
  return request<{ updated: number }>({
    url: `${PREFIX}/read`,
    method: 'PUT',
    data: body,
  })
}

/** 单条标记已读 */
export function markOneRead(notificationId: string) {
  return request<{ updated: number }>({
    url: `${PREFIX}/${notificationId}/read`,
    method: 'PUT',
  })
}
